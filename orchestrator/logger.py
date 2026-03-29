"""Structured JSON logger for the Notion Spec-to-Ship Pipeline."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any

STAGE_EVENTS = [
    "detected",
    "extracted",
    "spec_generated",
    "db_created",
    "tasks_written",
    "task_started",
    "task_completed",
    "task_failed",
    "run_completed",
]


class StructuredLogger:
    """Emits JSON log lines to stdout for every pipeline stage transition."""

    def log(
        self,
        run_id: str,
        stage: str,
        outcome: str,
        detail: dict[str, Any] | None = None,
    ) -> None:
        """Emit a single JSON log line to stdout.

        Args:
            run_id: UUID of the pipeline run.
            stage: One of STAGE_EVENTS.
            outcome: e.g. "success" or "failure".
            detail: Optional dict with additional context.
        """
        entry: dict[str, Any] = {
            "run_id": run_id,
            "stage": stage,
            "timestamp": datetime.now(tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%S.%f"
            )[:-3] + "Z",
            "outcome": outcome,
            "detail": detail,
        }
        print(json.dumps(entry), file=sys.stdout, flush=True)
