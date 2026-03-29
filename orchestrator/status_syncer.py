"""Status Syncer — thin wrapper around NotionWriter.update_task_status with logging."""

from __future__ import annotations

from orchestrator.errors import NotionWriteError, StatusSyncError
from orchestrator.logger import StructuredLogger
from orchestrator.models import TaskStatus
from orchestrator.notion_writer import NotionWriter

_STATUS_TO_STAGE = {
    TaskStatus.IN_PROGRESS: "task_started",
    TaskStatus.DONE: "task_completed",
    TaskStatus.FAILED: "task_failed",
    TaskStatus.TODO: "task_started",
}


class StatusSyncer:
    """Calls NotionWriter.update_task_status and logs every transition.

    Separated from NotionWriter for testability. Sync failures are caught and
    logged but never re-raised so the pipeline can continue.
    """

    def __init__(
        self,
        notion_writer: NotionWriter,
        logger: StructuredLogger,
        run_id: str,
    ) -> None:
        self._writer = notion_writer
        self._logger = logger
        self._run_id = run_id

    def sync(
        self,
        task_page_id: str,
        status: TaskStatus,
        error: str | None = None,
    ) -> None:
        """Update task status in Notion and log the transition.

        If NotionWriteError or StatusSyncError is raised, the failure is logged
        and the exception is suppressed so the pipeline continues.
        """
        stage = _STATUS_TO_STAGE.get(status, "task_started")
        try:
            self._writer.update_task_status(task_page_id, status, error)
            self._logger.log(
                self._run_id,
                stage,
                "success",
                {"task_page_id": task_page_id, "status": status.value},
            )
        except (NotionWriteError, StatusSyncError) as exc:
            self._logger.log(
                self._run_id,
                stage,
                "failure",
                {
                    "task_page_id": task_page_id,
                    "status": status.value,
                    "error": str(exc),
                },
            )
