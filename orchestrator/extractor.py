"""Idea Extractor — retrieves and concatenates plain text from a Notion page."""

from __future__ import annotations

from orchestrator.errors import EmptyIdeaError

# Block types that can have children worth recursing into
_CONTAINER_BLOCK_TYPES = {
    "toggle",
    "column_list",
    "column",
    "bulleted_list_item",
    "numbered_list_item",
    "quote",
    "callout",
    "synced_block",
    "template",
    "child_page",
    "child_database",
}

# Block types that carry rich_text directly
_RICH_TEXT_BLOCK_TYPES = {
    "paragraph",
    "heading_1",
    "heading_2",
    "heading_3",
    "bulleted_list_item",
    "numbered_list_item",
    "toggle",
    "quote",
    "callout",
    "code",
    "to_do",
}


def _extract_rich_text(block: dict) -> str:
    """Return concatenated plain_text from a block's rich_text array, if present."""
    block_type = block.get("type", "")
    type_data = block.get(block_type, {})
    rich_text = type_data.get("rich_text", [])
    return "".join(rt.get("plain_text", "") for rt in rich_text)


class IdeaExtractor:
    """Extracts plain-text content from a Notion page recursively."""

    def __init__(self, notion_client) -> None:
        """
        Args:
            notion_client: An object with a ``get_block_children(block_id, start_cursor=None)``
                           method that returns the Notion block-children response dict.
        """
        self._client = notion_client

    def _get_all_children(self, block_id: str) -> list[dict]:
        """Fetch all child blocks for *block_id*, following pagination."""
        results: list[dict] = []
        cursor: str | None = None

        while True:
            kwargs: dict = {}
            if cursor:
                kwargs["start_cursor"] = cursor

            response: dict = self._client.get_block_children(block_id, **kwargs)
            results.extend(response.get("results", []))

            if not response.get("has_more", False):
                break
            cursor = response.get("next_cursor")

        return results

    def _collect_text(self, block_id: str) -> str:
        """Recursively collect plain text from *block_id* and all descendants."""
        parts: list[str] = []

        for block in self._get_all_children(block_id):
            text = _extract_rich_text(block)
            if text:
                parts.append(text)

            # Recurse into children when the block reports it has them
            if block.get("has_children", False):
                child_text = self._collect_text(block["id"])
                if child_text:
                    parts.append(child_text)

        return "\n".join(parts)

    def extract(self, page_id: str) -> str:
        """Return plain-text content of the page (recursive).

        Raises:
            EmptyIdeaError: if the resulting text is fewer than 10 characters.
        """
        text = self._collect_text(page_id)

        if len(text) < 10:
            raise EmptyIdeaError(
                f"Page {page_id!r} content is too short ({len(text)} chars); "
                "at least 10 characters are required."
            )

        return text
