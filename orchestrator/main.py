"""Orchestrator entry point — pipeline lifecycle and state management."""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from orchestrator.agent_driver import CodingAgentDriver
from orchestrator.errors import EmptyIdeaError, MCPConnectionError, NotionWriteError, SpecGenerationError, TaskExecutionError
from orchestrator.extractor import IdeaExtractor
from orchestrator.models import PipelineRun, RunStatus, Spec, TaskRecord, TaskStatus
from orchestrator.logger import StructuredLogger
from orchestrator.notion_writer import NotionWriter
from orchestrator.poller import POLL_INTERVAL, Poller, _compute_hash
from orchestrator.spec_generator import SpecGenerator
from orchestrator.status_syncer import StatusSyncer

STATE_FILE = os.environ.get("STATE_FILE", "state.json")


# ---------------------------------------------------------------------------
# State persistence helpers
# ---------------------------------------------------------------------------

def _load_state(path: str = STATE_FILE) -> dict:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"seen_pages": {}, "active_runs": {}}


def _save_state(state: dict, path: str = STATE_FILE) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, default=str)


def _pipeline_run_to_dict(run: PipelineRun) -> dict:
    return {
        "idea_page_id": run.idea_page_id,
        "status": run.status.value,
        "started_at": run.started_at.isoformat(),
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "tasks": [
            {
                "order": t.order,
                "title": t.title,
                "notion_page_id": t.notion_page_id,
                "status": t.status.value,
                "error": t.error,
            }
            for t in run.tasks
        ],
    }


def _pipeline_run_from_dict(run_id: str, data: dict) -> PipelineRun:
    tasks = [
        TaskRecord(
            order=t["order"],
            title=t["title"],
            notion_page_id=t["notion_page_id"],
            status=TaskStatus(t["status"]),
            error=t.get("error"),
        )
        for t in data.get("tasks", [])
    ]
    started_at_raw = data.get("started_at", "")
    try:
        started_at = datetime.fromisoformat(started_at_raw)
    except (ValueError, TypeError):
        started_at = datetime.now(tz=timezone.utc)

    finished_at = None
    finished_at_raw = data.get("finished_at")
    if finished_at_raw:
        try:
            finished_at = datetime.fromisoformat(finished_at_raw)
        except (ValueError, TypeError):
            finished_at = None

    return PipelineRun(
        run_id=run_id,
        idea_page_id=data.get("idea_page_id", ""),
        status=RunStatus(data.get("status", RunStatus.PENDING.value)),
        started_at=started_at,
        finished_at=finished_at,
        tasks=tasks,
    )


def _persist_run(run: PipelineRun, state_file: str = STATE_FILE) -> None:
    """Write the current PipelineRun into state.json under active_runs."""
    state = _load_state(state_file)
    state.setdefault("active_runs", {})[run.run_id] = _pipeline_run_to_dict(run)
    _save_state(state, state_file)


# ---------------------------------------------------------------------------
# Run summary
# ---------------------------------------------------------------------------

def _print_summary(run: PipelineRun) -> None:
    completed = sum(1 for t in run.tasks if t.status == TaskStatus.DONE)
    failed = sum(1 for t in run.tasks if t.status == TaskStatus.FAILED)
    total = len(run.tasks)

    if run.finished_at and run.started_at:
        elapsed = (run.finished_at - run.started_at).total_seconds()
    else:
        elapsed = 0.0

    print("=== Pipeline Run Summary ===")
    print(f"Run ID:          {run.run_id}")
    print(f"Idea Page ID:    {run.idea_page_id}")
    print(f"Total Tasks:     {total}")
    print(f"Tasks Completed: {completed}")
    print(f"Tasks Failed:    {failed}")
    print(f"Total Elapsed:   {elapsed:.1f}s")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_pipeline(
    page_id: str,
    *,
    notion_client: Any = None,
    llm_client: Any = None,
    extractor: IdeaExtractor | None = None,
    spec_generator: SpecGenerator | None = None,
    notion_writer: NotionWriter | None = None,
    agent_driver: CodingAgentDriver | None = None,
    status_syncer: StatusSyncer | None = None,
    state_file: str = STATE_FILE,
    logger: StructuredLogger | None = None,
) -> PipelineRun:
    """Create and execute a PipelineRun for *page_id*.

    Stages wired so far (tasks 13.1–13.2):
    1. Checks the MCP connection (raises MCPConnectionError / exits on failure).
    2. Creates a PipelineRun with a fresh UUID and logs ``detected``.
    3. Extracts idea text via IdeaExtractor; logs ``extracted``.
       On EmptyIdeaError: logs warning, marks run FAILED, persists, returns early.
    4. Generates a Spec via SpecGenerator; logs ``spec_generated``.
       On SpecGenerationError: logs failure, marks run FAILED, persists, returns early.
    5. Writes spec to Notion (NotionWriter): creates Spec_DB, writes task rows,
       writes spec blocks, updates Idea_Page with DB link.
       Logs ``db_created`` and ``tasks_written``.
       On NotionWriteError (critical steps): marks run FAILED, persists, returns early.
       Best-effort steps (write_spec_blocks, update_idea_page_completion) do not halt.
    6. Marks run DONE, persists, logs ``run_completed``, prints summary.

    Args:
        page_id: Notion page ID of the idea to process.
        notion_client: Injected Notion client (reads NOTION_MCP_URL from env
            when None).
        llm_client: Injected LLM client (reads LLM_API_KEY from env when None).
        extractor: Injected IdeaExtractor; created from notion_client when None
            (skipped when notion_client is also None).
        spec_generator: Injected SpecGenerator; created from llm_client when None
            (skipped when llm_client is also None).
        notion_writer: Injected NotionWriter; created from notion_client when None
            (skipped when notion_client is also None).
        agent_driver: Injected CodingAgentDriver; created when None and tasks exist.
        status_syncer: Injected StatusSyncer; created when None and tasks exist.
        state_file: Path to the state JSON file.
        logger: Injected StructuredLogger; a default instance is created when None.
    """
    if logger is None:
        logger = StructuredLogger()

    # Resolve notion_client from environment when not injected
    if notion_client is None:
        notion_client = _default_notion_client()
    
    # Resolve llm_client from environment when not injected
    if llm_client is None:
        llm_client = _default_llm_client()

    # Check MCP connection at startup
    _check_mcp_connection(notion_client)

    run_id = str(uuid.uuid4())
    now = datetime.now(tz=timezone.utc)

    run = PipelineRun(
        run_id=run_id,
        idea_page_id=page_id,
        status=RunStatus.RUNNING,
        started_at=now,
    )

    _persist_run(run, state_file)
    logger.log(run_id, "detected", "success", {"idea_page_id": page_id})

    # ------------------------------------------------------------------
    # Stage 2: Extract idea text
    # ------------------------------------------------------------------
    spec: Spec | None = None

    # Resolve extractor
    if extractor is None and notion_client is not None:
        extractor = IdeaExtractor(notion_client)

    if extractor is not None:
        try:
            idea_text = extractor.extract(page_id)
        except EmptyIdeaError as exc:
            logger.log(run_id, "extracted", "failure", {"error": str(exc)})
            run.status = RunStatus.FAILED
            run.finished_at = datetime.now(tz=timezone.utc)
            _persist_run(run, state_file)
            return run

        logger.log(run_id, "extracted", "success", {"idea_page_id": page_id})

        # ------------------------------------------------------------------
        # Stage 3: Generate spec
        # ------------------------------------------------------------------
        if spec_generator is None and llm_client is not None:
            spec_generator = SpecGenerator(llm_client)

        if spec_generator is not None:
            try:
                spec = spec_generator.generate(idea_text)
            except SpecGenerationError as exc:
                logger.log(run_id, "spec_generated", "failure", {"error": str(exc)})
                run.status = RunStatus.FAILED
                run.finished_at = datetime.now(tz=timezone.utc)
                _persist_run(run, state_file)
                return run

            logger.log(run_id, "spec_generated", "success", {"idea_page_id": page_id})

    # Store spec for use in subsequent pipeline stages (task 13.2)
    run._spec = spec  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Stage 4: Notion write-back (task 13.2)
    # ------------------------------------------------------------------
    if spec is not None and notion_client is not None:
        # Resolve notion_writer
        if notion_writer is None:
            notion_writer = NotionWriter(notion_client)

        # 4a. Create Spec_DB
        try:
            db_id = notion_writer.create_spec_db(page_id, spec)
        except NotionWriteError as exc:
            logger.log(run_id, "db_created", "failure", {"error": str(exc)})
            run.status = RunStatus.FAILED
            run.finished_at = datetime.now(tz=timezone.utc)
            _persist_run(run, state_file)
            return run

        logger.log(run_id, "db_created", "success", {"db_id": db_id})

        # 4b. Write task rows
        try:
            task_page_ids = notion_writer.write_tasks(db_id, spec.tasks, run_id=run_id)
        except NotionWriteError as exc:
            logger.log(run_id, "tasks_written", "failure", {"error": str(exc)})
            run.status = RunStatus.FAILED
            run.finished_at = datetime.now(tz=timezone.utc)
            _persist_run(run, state_file)
            return run

        run.tasks = [
            TaskRecord(
                order=task.order,
                title=task.title,
                notion_page_id=pid,
                status=TaskStatus.TODO,
            )
            for task, pid in zip(spec.tasks, task_page_ids)
        ]
        logger.log(run_id, "tasks_written", "success", {"task_count": len(run.tasks)})

        # 4c. Write spec blocks (best-effort)
        try:
            notion_writer.write_spec_blocks(page_id, spec)
        except NotionWriteError:
            pass

        # 4d. Update Idea_Page with DB link (best-effort) — updated after task loop
        try:
            notion_writer.update_idea_page_completion(page_id, db_id, summary="")
        except NotionWriteError:
            pass

    # ------------------------------------------------------------------
    # Stage 5: Task execution loop (task 13.3)
    # ------------------------------------------------------------------
    if run.tasks:
        # Resolve agent_driver
        if agent_driver is None:
            agent_driver = CodingAgentDriver()

        # Resolve status_syncer — requires notion_writer
        if status_syncer is None and notion_writer is not None:
            status_syncer = StatusSyncer(notion_writer, logger, run_id)

        # Sort tasks by order ascending
        sorted_tasks = sorted(run.tasks, key=lambda t: t.order)

        for task_record in sorted_tasks:
            # a. Mark In Progress and log task_started
            if status_syncer is not None:
                status_syncer.sync(task_record.notion_page_id, TaskStatus.IN_PROGRESS)
            task_record.status = TaskStatus.IN_PROGRESS
            _persist_run(run, state_file)

            # d. Find corresponding Task from spec by matching order
            task_obj = None
            if spec is not None:
                for t in spec.tasks:
                    if t.order == task_record.order:
                        task_obj = t
                        break

            # e–g. Execute task and handle result
            try:
                if task_obj is not None and agent_driver is not None:
                    result = agent_driver.execute_task(task_obj)
                else:
                    # No spec task found — treat as failure
                    result = None

                if result is not None and result.success:
                    task_record.status = TaskStatus.DONE
                    if status_syncer is not None:
                        status_syncer.sync(task_record.notion_page_id, TaskStatus.DONE)
                else:
                    error_msg = (result.error or "Task failed") if result is not None else "No task definition found"
                    task_record.status = TaskStatus.FAILED
                    task_record.error = error_msg
                    if status_syncer is not None:
                        status_syncer.sync(task_record.notion_page_id, TaskStatus.FAILED, error=error_msg)

            except TaskExecutionError as exc:
                task_record.status = TaskStatus.FAILED
                task_record.error = str(exc)
                if status_syncer is not None:
                    status_syncer.sync(task_record.notion_page_id, TaskStatus.FAILED, error=task_record.error)
                # Continue to next task — do NOT halt pipeline

            _persist_run(run, state_file)

    run.status = RunStatus.DONE
    run.finished_at = datetime.now(tz=timezone.utc)
    _persist_run(run, state_file)

    done_count = sum(1 for t in run.tasks if t.status == TaskStatus.DONE)
    failed_count = sum(1 for t in run.tasks if t.status == TaskStatus.FAILED)
    summary = f"{done_count} task(s) done, {failed_count} task(s) failed"

    logger.log(run_id, "run_completed", "success", {"idea_page_id": page_id, "summary": summary})
    _print_summary(run)

    return run


def get_run_status(run_id: str, state_file: str = STATE_FILE) -> PipelineRun:
    """Return the PipelineRun for *run_id* by reading state.json.

    Raises:
        KeyError: if *run_id* is not found in active_runs.
    """
    state = _load_state(state_file)
    active_runs: dict = state.get("active_runs", {})
    if run_id not in active_runs:
        raise KeyError(f"Run ID {run_id!r} not found in state.json")
    return _pipeline_run_from_dict(run_id, active_runs[run_id])


# ---------------------------------------------------------------------------
# Poller loop
# ---------------------------------------------------------------------------

def start_poller(
    notion_client: Any = None,
    state_file: str = STATE_FILE,
) -> None:
    """Run the polling loop indefinitely, spawning run_pipeline for each new page.

    Creates a :class:`~orchestrator.poller.Poller` instance and enters an
    infinite loop that:

    1. Calls ``poller.poll()`` to get new page IDs.
    2. For each page ID, marks it as seen and spawns ``run_pipeline`` in a
       daemon thread.
    3. Sleeps for ``POLL_INTERVAL`` seconds (30 s).

    The loop exits cleanly on :exc:`KeyboardInterrupt`.

    Args:
        notion_client: Injected Notion client; passed through to both the
            :class:`~orchestrator.poller.Poller` and :func:`run_pipeline`.
        state_file: Path to the state JSON file.
    """
    poller = Poller(notion_client=notion_client, state_file=state_file)

    try:
        while True:
            new_page_ids = poller.poll()
            for page_id in new_page_ids:
                # Use page_id as a placeholder hash so the page is not
                # re-queued before the pipeline has a chance to run.
                poller.mark_seen(page_id, _compute_hash(page_id))
                threading.Thread(
                    target=run_pipeline,
                    args=(page_id,),
                    kwargs={"notion_client": notion_client, "state_file": state_file},
                    daemon=True,
                ).start()
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        return


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _default_notion_client() -> Any:
    """Return a Notion client if NOTION_API_KEY is set, otherwise None."""
    import os
    if os.environ.get("NOTION_API_KEY"):
        from orchestrator.notion_mcp_client import NotionMCPClient
        return NotionMCPClient()
    return None


def _default_llm_client() -> Any:
    """Return a Groq LLM client if GROQ_API_KEY is set, otherwise None."""
    import os
    if os.environ.get("GROQ_API_KEY"):
        from orchestrator.groq_client import GroqClient
        return GroqClient()
    return None


def _check_mcp_connection(notion_client: Any) -> None:
    """Verify the MCP connection is available.

    Calls ``notion_client.ping()`` when the client exposes it.  If the client
    raises ``MCPConnectionError`` (or is None and the env var is set to require
    a connection), this function re-raises so the caller can exit non-zero.
    """
    if notion_client is None:
        # No client injected and no env var — skip check in skeleton mode
        return

    if hasattr(notion_client, "ping"):
        try:
            notion_client.ping()
        except MCPConnectionError:
            raise
        except Exception as exc:
            raise MCPConnectionError(
                f"Failed to connect to Notion MCP: {exc}"
            ) from exc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _cmd_status(args: argparse.Namespace) -> None:
    try:
        run = get_run_status(args.run_id, state_file=STATE_FILE)
    except KeyError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    _print_summary(run)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="orchestrator",
        description="Notion Spec-to-Ship Pipeline CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    status_parser = subparsers.add_parser("status", help="Show run status")
    status_parser.add_argument("run_id", help="Pipeline run UUID")

    subparsers.add_parser("run", help="Start the poller loop")

    args = parser.parse_args(argv)

    if args.command == "status":
        _cmd_status(args)
    elif args.command == "run":
        start_poller()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except MCPConnectionError as exc:
        print(f"Error: MCP connection failed — {exc}", file=sys.stderr)
        sys.exit(1)
