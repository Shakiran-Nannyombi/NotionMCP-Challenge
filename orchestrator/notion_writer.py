"""Notion Writer — all Spec_DB and Idea_Page write operations."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from orchestrator.errors import NotionWriteError
from orchestrator.models import Spec, Task, TaskStatus
from orchestrator.retry import retry


def _retrying(fn):
    """Apply @retry(3 attempts, exponential backoff) and re-raise as NotionWriteError."""
    retried = retry(max_attempts=3, backoff_base=1.0, backoff_factor=2.0)(fn)

    import functools

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return retried(*args, **kwargs)
        except Exception as exc:
            raise NotionWriteError(str(exc)) from exc

    return wrapper


class NotionWriter:
    """Writes spec data and task rows to Notion via the injected notion_client."""

    def __init__(self, notion_client) -> None:
        self._client = notion_client

    @_retrying
    def create_spec_db(self, parent_page_id: str, spec: Spec) -> str:
        """Creates Spec_DB under *parent_page_id*, returns the new database_id."""
        payload = {
            "parent": {"type": "page_id", "page_id": parent_page_id},
            "title": [{"type": "text", "text": {"content": "Spec DB"}}],
            "properties": {
                "Task Title": {"title": {}},
                "Description": {"rich_text": {}},
                "Acceptance Criteria": {"rich_text": {}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "To Do", "color": "gray"},
                            {"name": "In Progress", "color": "blue"},
                            {"name": "Done", "color": "green"},
                            {"name": "Failed", "color": "red"},
                        ]
                    }
                },
                "Order": {"number": {"format": "number"}},
                "Run ID": {"rich_text": {}},
                "Error": {"rich_text": {}},
            },
        }
        result = self._client.create_database(payload)
        return result["id"]

    @_retrying
    def write_tasks(self, database_id: str, tasks: list[Task], run_id: str = "") -> list[str]:
        """Writes each task as a DB row with Status = To Do.

        Enforces a 350 ms delay between consecutive API calls to respect the
        Notion 3 req/s rate limit.  Returns the list of created page_ids.
        """
        page_ids: list[str] = []
        for i, task in enumerate(tasks):
            if i > 0:
                time.sleep(0.35)
            payload = {
                "parent": {"database_id": database_id},
                "properties": {
                    "Task Title": {
                        "title": [{"type": "text", "text": {"content": task.title}}]
                    },
                    "Description": {
                        "rich_text": [{"type": "text", "text": {"content": task.description}}]
                    },
                    "Acceptance Criteria": {
                        "rich_text": [
                            {"type": "text", "text": {"content": task.acceptance_criteria}}
                        ]
                    },
                    "Status": {"select": {"name": TaskStatus.TODO.value}},
                    "Order": {"number": task.order},
                    "Run ID": {
                        "rich_text": [{"type": "text", "text": {"content": run_id}}]
                    },
                    "Error": {"rich_text": []},
                },
            }
            result = self._client.create_page(payload)
            page_ids.append(result["id"])
        return page_ids

    @_retrying
    def write_spec_blocks(self, page_id: str, spec: Spec) -> None:
        """Appends requirements + design as formatted blocks to the Idea_Page."""
        children = []

        # Introduction heading + paragraph
        children.append(
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Introduction"}}]
                },
            }
        )
        children.append(
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": spec.introduction}}]
                },
            }
        )

        # Requirements section
        children.append(
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": "Requirements"}}]
                },
            }
        )
        for req in spec.requirements:
            children.append(
                {
                    "object": "block",
                    "type": "heading_3",
                    "heading_3": {
                        "rich_text": [
                            {"type": "text", "text": {"content": f"{req.id}: {req.title}"}}
                        ]
                    },
                }
            )
            children.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"type": "text", "text": {"content": req.user_story}}]
                    },
                }
            )
            for criterion in req.acceptance_criteria:
                children.append(
                    {
                        "object": "block",
                        "type": "bulleted_list_item",
                        "bulleted_list_item": {
                            "rich_text": [{"type": "text", "text": {"content": criterion}}]
                        },
                    }
                )

        self._client.append_block_children(page_id, children)

    @_retrying
    def update_task_status(
        self,
        task_page_id: str,
        status: TaskStatus,
        error: str | None = None,
    ) -> None:
        """Updates the Status select on a task row.

        When *status* is Failed, also writes *error* into the Error rich_text
        property.
        """
        properties: dict = {
            "Status": {"select": {"name": status.value}},
        }
        if status == TaskStatus.FAILED and error:
            properties["Error"] = {
                "rich_text": [{"type": "text", "text": {"content": error}}]
            }
        self._client.update_page(task_page_id, properties)

    @_retrying
    def update_idea_page_completion(
        self, page_id: str, db_id: str, summary: str
    ) -> None:
        """Appends a Spec_DB link and completion timestamp block to the Idea_Page."""
        timestamp = datetime.now(tz=timezone.utc).isoformat()
        children = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {"type": "text", "text": {"content": "Pipeline Completed"}}
                    ]
                },
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": f"Completed at: {timestamp}"}},
                    ]
                },
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": summary}},
                    ]
                },
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": f"Spec DB ID: {db_id}",
                            },
                        }
                    ]
                },
            },
        ]
        self._client.append_block_children(page_id, children)
