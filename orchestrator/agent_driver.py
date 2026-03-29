"""Coding Agent Driver — invokes Kiro via subprocess for each task."""

from __future__ import annotations

import subprocess
import tempfile
import os
from typing import List

from orchestrator.errors import TaskExecutionError
from orchestrator.models import Task, TaskResult


class CodingAgentDriver:
    def __init__(self, command: List[str] | None = None) -> None:
        self.command = command if command is not None else ["kiro"]

    def execute_task(self, task: Task) -> TaskResult:
        """Runs the coding agent for a single task. Returns success/failure + output."""
        prompt = (
            f"Task: {task.title}\n\n"
            f"Description:\n{task.description}\n\n"
            f"Acceptance Criteria:\n{task.acceptance_criteria}\n"
        )

        tmp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as tmp:
                tmp.write(prompt)
                tmp_path = tmp.name

            try:
                result = subprocess.run(
                    self.command + [tmp_path],
                    capture_output=True,
                    text=True,
                )
            except (FileNotFoundError, OSError) as exc:
                raise TaskExecutionError(
                    f"Failed to launch coding agent '{self.command[0]}': {exc}"
                ) from exc

            stdout = result.stdout or ""
            stderr = result.stderr or ""

            if result.returncode == 0:
                return TaskResult(success=True, output=stdout)
            return TaskResult(success=False, output=stdout, error=stderr)

        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
