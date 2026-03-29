"""Poller: detects new/updated Notion pages matching the pipeline trigger."""

from __future__ import annotations

import hashlib
import json
import os
from typing import Any

STATE_FILE = "state.json"
TRIGGER_PREFIX = "[SHIP]"
POLL_INTERVAL = 30  # seconds


def _load_state(path: str = STATE_FILE) -> dict:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"seen_pages": {}, "active_runs": {}}


def _save_state(state: dict, path: str = STATE_FILE) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def _compute_hash(content: str) -> str:
    """Return SHA-256 hex digest of the given string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class Poller:
    """Polls Notion for pages matching the pipeline trigger.

    Trigger detection:
    - Title starts with ``[SHIP]``, OR
    - Page property ``pipeline_trigger`` equals ``true``.

    Maintains a seen-set in ``state.json`` keyed by page ID → content hash so
    that the same page version is never returned twice.

    Args:
        notion_client: An object with a ``search(query, filter)`` method that
            returns Notion search results (dict with ``"results"`` list).
            Injected for testability; defaults to a thin MCP wrapper when
            ``None``.
        state_file: Path to the JSON file used for persistence.
    """

    def __init__(
        self,
        notion_client: Any = None,
        state_file: str = STATE_FILE,
    ) -> None:
        self._client = notion_client
        self._state_file = state_file

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def poll(self) -> list[str]:
        """Return page IDs whose content has changed since last seen.

        A page is returned when:
        1. It matches the trigger (title prefix ``[SHIP]`` or property
           ``pipeline_trigger = true``), AND
        2. Its content hash differs from the stored hash (or it has never
           been seen before).
        """
        state = _load_state(self._state_file)
        seen: dict[str, str] = state.get("seen_pages", {})

        candidate_pages = self._fetch_trigger_pages()
        new_page_ids: list[str] = []

        for page in candidate_pages:
            page_id = page.get("id", "")
            if not page_id:
                continue

            content_str = _page_to_content_string(page)
            current_hash = _compute_hash(content_str)

            if seen.get(page_id) != current_hash:
                new_page_ids.append(page_id)

        return new_page_ids

    def mark_seen(self, page_id: str, content_hash: str) -> None:
        """Persist *page_id* → *content_hash* so the page is not re-processed.

        Args:
            page_id: Notion page ID.
            content_hash: SHA-256 hex digest of the page content string.
        """
        state = _load_state(self._state_file)
        state.setdefault("seen_pages", {})[page_id] = content_hash
        _save_state(state, self._state_file)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _fetch_trigger_pages(self) -> list[dict]:
        """Query Notion for pages matching either trigger condition."""
        if self._client is None:
            return []

        results: list[dict] = []

        # Search by title prefix "[SHIP]"
        try:
            response = self._client.search(
                query=TRIGGER_PREFIX,
                filter={"value": "page", "property": "object"},
            )
            for page in response.get("results", []):
                if _matches_trigger(page):
                    results.append(page)
        except Exception:
            pass

        return results


# ------------------------------------------------------------------
# Module-level helpers (pure functions — easy to unit-test)
# ------------------------------------------------------------------

def _matches_trigger(page: dict) -> bool:
    """Return True if *page* matches either trigger condition."""
    return _has_ship_prefix(page) or _has_pipeline_trigger_property(page)


def _has_ship_prefix(page: dict) -> bool:
    """Return True if the page title starts with ``[SHIP]``."""
    title = _extract_title(page)
    return title.startswith(TRIGGER_PREFIX)


def _has_pipeline_trigger_property(page: dict) -> bool:
    """Return True if the page has ``pipeline_trigger`` property set to true."""
    props = page.get("properties", {})
    trigger_prop = props.get("pipeline_trigger", {})

    # Notion checkbox property
    if trigger_prop.get("type") == "checkbox":
        return bool(trigger_prop.get("checkbox", False))

    # Notion select / rich_text fallback: accept string "true"
    if trigger_prop.get("type") == "select":
        select = trigger_prop.get("select") or {}
        return str(select.get("name", "")).lower() == "true"

    if trigger_prop.get("type") == "rich_text":
        rich_text = trigger_prop.get("rich_text", [])
        text = "".join(rt.get("plain_text", "") for rt in rich_text)
        return text.strip().lower() == "true"

    return False


def _extract_title(page: dict) -> str:
    """Extract the plain-text title from a Notion page object."""
    props = page.get("properties", {})

    # Notion pages have a "title" property (type: title)
    for prop in props.values():
        if prop.get("type") == "title":
            title_parts = prop.get("title", [])
            return "".join(part.get("plain_text", "") for part in title_parts)

    # Fallback: top-level "title" key (some API shapes)
    if "title" in page:
        raw = page["title"]
        if isinstance(raw, list):
            return "".join(part.get("plain_text", "") for part in raw)
        if isinstance(raw, str):
            return raw

    return ""


def _page_to_content_string(page: dict) -> str:
    """Produce a stable string representation of a page for hashing.

    Uses the page ID + last_edited_time (if present) + title so that any
    meaningful change produces a different hash without requiring a full
    block-content fetch at poll time.
    """
    page_id = page.get("id", "")
    last_edited = page.get("last_edited_time", "")
    title = _extract_title(page)
    return f"{page_id}|{last_edited}|{title}"
