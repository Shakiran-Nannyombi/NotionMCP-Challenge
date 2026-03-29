"""Unit tests for StatusSyncer."""

from __future__ import annotations

from unittest.mock import MagicMock, call

import pytest

from orchestrator.errors import NotionWriteError, StatusSyncError
from orchestrator.models import TaskStatus
from orchestrator.status_syncer import StatusSyncer


def _make_syncer(writer=None, logger=None, run_id="run-123"):
    writer = writer or MagicMock()
    logger = logger or MagicMock()
    return StatusSyncer(writer, logger, run_id), writer, logger


class TestStatusSyncerHappyPath:
    def test_calls_update_task_status(self):
        syncer, writer, _ = _make_syncer()
        syncer.sync("page-1", TaskStatus.IN_PROGRESS)
        writer.update_task_status.assert_called_once_with("page-1", TaskStatus.IN_PROGRESS, None)

    def test_passes_error_to_writer(self):
        syncer, writer, _ = _make_syncer()
        syncer.sync("page-1", TaskStatus.FAILED, error="boom")
        writer.update_task_status.assert_called_once_with("page-1", TaskStatus.FAILED, "boom")

    def test_logs_success_on_in_progress(self):
        syncer, _, logger = _make_syncer()
        syncer.sync("page-1", TaskStatus.IN_PROGRESS)
        logger.log.assert_called_once()
        args = logger.log.call_args[0]
        assert args[0] == "run-123"
        assert args[1] == "task_started"
        assert args[2] == "success"

    def test_logs_success_on_done(self):
        syncer, _, logger = _make_syncer()
        syncer.sync("page-1", TaskStatus.DONE)
        args = logger.log.call_args[0]
        assert args[1] == "task_completed"
        assert args[2] == "success"

    def test_logs_success_on_failed(self):
        syncer, _, logger = _make_syncer()
        syncer.sync("page-1", TaskStatus.FAILED, error="oops")
        args = logger.log.call_args[0]
        assert args[1] == "task_failed"
        assert args[2] == "success"

    def test_log_detail_contains_page_id_and_status(self):
        syncer, _, logger = _make_syncer()
        syncer.sync("page-42", TaskStatus.DONE)
        detail = logger.log.call_args[0][3]
        assert detail["task_page_id"] == "page-42"
        assert detail["status"] == TaskStatus.DONE.value


class TestStatusSyncerFailureIsolation:
    def test_notion_write_error_does_not_raise(self):
        writer = MagicMock()
        writer.update_task_status.side_effect = NotionWriteError("mcp down")
        syncer, _, _ = _make_syncer(writer=writer)
        # Must not raise
        syncer.sync("page-1", TaskStatus.IN_PROGRESS)

    def test_status_sync_error_does_not_raise(self):
        writer = MagicMock()
        writer.update_task_status.side_effect = StatusSyncError("sync failed")
        syncer, _, _ = _make_syncer(writer=writer)
        syncer.sync("page-1", TaskStatus.DONE)

    def test_logs_failure_on_notion_write_error(self):
        writer = MagicMock()
        writer.update_task_status.side_effect = NotionWriteError("mcp down")
        syncer, _, logger = _make_syncer(writer=writer)
        syncer.sync("page-1", TaskStatus.IN_PROGRESS)
        args = logger.log.call_args[0]
        assert args[2] == "failure"
        assert "mcp down" in args[3]["error"]

    def test_logs_failure_on_status_sync_error(self):
        writer = MagicMock()
        writer.update_task_status.side_effect = StatusSyncError("sync failed")
        syncer, _, logger = _make_syncer(writer=writer)
        syncer.sync("page-1", TaskStatus.DONE)
        args = logger.log.call_args[0]
        assert args[2] == "failure"

    def test_pipeline_continues_after_sync_failure(self):
        """Simulate two consecutive sync calls; first fails, second must still execute."""
        writer = MagicMock()
        writer.update_task_status.side_effect = [NotionWriteError("fail"), None]
        syncer, _, logger = _make_syncer(writer=writer)

        syncer.sync("page-1", TaskStatus.IN_PROGRESS)
        syncer.sync("page-2", TaskStatus.DONE)

        assert writer.update_task_status.call_count == 2
        assert logger.log.call_count == 2
