"""Unit tests for orchestrator/poller.py."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile

import pytest

from orchestrator.poller import (
    Poller,
    _compute_hash,
    _extract_title,
    _has_pipeline_trigger_property,
    _has_ship_prefix,
    _matches_trigger,
    _page_to_content_string,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_page(
    page_id: str = "page-1",
    title: str = "My Page",
    last_edited: str = "2025-01-01T00:00:00.000Z",
    pipeline_trigger: bool | None = None,
) -> dict:
    """Build a minimal Notion page dict."""
    props: dict = {
        "Name": {
            "type": "title",
            "title": [{"plain_text": title}],
        }
    }
    if pipeline_trigger is not None:
        props["pipeline_trigger"] = {
            "type": "checkbox",
            "checkbox": pipeline_trigger,
        }
    return {
        "id": page_id,
        "last_edited_time": last_edited,
        "properties": props,
    }


class FakeNotionClient:
    """Minimal fake that returns a fixed list of pages."""

    def __init__(self, pages: list[dict]) -> None:
        self._pages = pages
        self.calls: list[dict] = []

    def search(self, query: str, filter: dict) -> dict:
        self.calls.append({"query": query, "filter": filter})
        return {"results": self._pages}


# ---------------------------------------------------------------------------
# _compute_hash
# ---------------------------------------------------------------------------

def test_compute_hash_returns_sha256():
    text = "hello"
    expected = hashlib.sha256(b"hello").hexdigest()
    assert _compute_hash(text) == expected


def test_compute_hash_empty_string():
    result = _compute_hash("")
    assert len(result) == 64  # SHA-256 hex is always 64 chars


# ---------------------------------------------------------------------------
# _extract_title
# ---------------------------------------------------------------------------

def test_extract_title_from_title_property():
    page = _make_page(title="[SHIP] My Idea")
    assert _extract_title(page) == "[SHIP] My Idea"


def test_extract_title_empty_when_no_title():
    assert _extract_title({}) == ""


def test_extract_title_fallback_string():
    page = {"title": "Direct Title"}
    assert _extract_title(page) == "Direct Title"


# ---------------------------------------------------------------------------
# _has_ship_prefix
# ---------------------------------------------------------------------------

def test_has_ship_prefix_true():
    assert _has_ship_prefix(_make_page(title="[SHIP] Build something")) is True


def test_has_ship_prefix_false():
    assert _has_ship_prefix(_make_page(title="Regular page")) is False


def test_has_ship_prefix_case_sensitive():
    # Trigger is case-sensitive per spec
    assert _has_ship_prefix(_make_page(title="[ship] lowercase")) is False


# ---------------------------------------------------------------------------
# _has_pipeline_trigger_property
# ---------------------------------------------------------------------------

def test_pipeline_trigger_checkbox_true():
    page = _make_page(pipeline_trigger=True)
    assert _has_pipeline_trigger_property(page) is True


def test_pipeline_trigger_checkbox_false():
    page = _make_page(pipeline_trigger=False)
    assert _has_pipeline_trigger_property(page) is False


def test_pipeline_trigger_missing():
    page = _make_page()  # no pipeline_trigger property
    assert _has_pipeline_trigger_property(page) is False


def test_pipeline_trigger_select_true():
    page = {
        "id": "p1",
        "properties": {
            "pipeline_trigger": {
                "type": "select",
                "select": {"name": "true"},
            }
        },
    }
    assert _has_pipeline_trigger_property(page) is True


def test_pipeline_trigger_rich_text_true():
    page = {
        "id": "p1",
        "properties": {
            "pipeline_trigger": {
                "type": "rich_text",
                "rich_text": [{"plain_text": "true"}],
            }
        },
    }
    assert _has_pipeline_trigger_property(page) is True


# ---------------------------------------------------------------------------
# _matches_trigger
# ---------------------------------------------------------------------------

def test_matches_trigger_ship_prefix():
    assert _matches_trigger(_make_page(title="[SHIP] Idea")) is True


def test_matches_trigger_property():
    assert _matches_trigger(_make_page(pipeline_trigger=True)) is True


def test_matches_trigger_neither():
    assert _matches_trigger(_make_page(title="Normal", pipeline_trigger=False)) is False


# ---------------------------------------------------------------------------
# Poller.poll
# ---------------------------------------------------------------------------

def test_poll_returns_new_pages(tmp_path):
    page = _make_page(page_id="abc", title="[SHIP] New Idea")
    client = FakeNotionClient([page])
    poller = Poller(notion_client=client, state_file=str(tmp_path / "state.json"))

    result = poller.poll()
    assert result == ["abc"]


def test_poll_excludes_seen_pages(tmp_path):
    page = _make_page(page_id="abc", title="[SHIP] Seen Idea", last_edited="2025-01-01T00:00:00Z")
    client = FakeNotionClient([page])
    state_file = str(tmp_path / "state.json")
    poller = Poller(notion_client=client, state_file=state_file)

    # Mark the page as seen with the same hash it would produce
    from orchestrator.poller import _page_to_content_string, _compute_hash
    content_hash = _compute_hash(_page_to_content_string(page))
    poller.mark_seen("abc", content_hash)

    result = poller.poll()
    assert result == []


def test_poll_returns_page_when_hash_changed(tmp_path):
    page = _make_page(page_id="abc", title="[SHIP] Updated", last_edited="2025-01-02T00:00:00Z")
    client = FakeNotionClient([page])
    state_file = str(tmp_path / "state.json")
    poller = Poller(notion_client=client, state_file=state_file)

    # Store an old hash
    poller.mark_seen("abc", "old_hash_value")

    result = poller.poll()
    assert "abc" in result


def test_poll_no_client_returns_empty(tmp_path):
    poller = Poller(notion_client=None, state_file=str(tmp_path / "state.json"))
    assert poller.poll() == []


def test_poll_ignores_non_trigger_pages(tmp_path):
    page = _make_page(page_id="xyz", title="Regular page", pipeline_trigger=False)
    client = FakeNotionClient([page])
    poller = Poller(notion_client=client, state_file=str(tmp_path / "state.json"))

    result = poller.poll()
    assert result == []


# ---------------------------------------------------------------------------
# Poller.mark_seen
# ---------------------------------------------------------------------------

def test_mark_seen_persists_to_state_file(tmp_path):
    state_file = str(tmp_path / "state.json")
    poller = Poller(notion_client=None, state_file=state_file)

    poller.mark_seen("page-42", "deadbeef")

    with open(state_file) as f:
        state = json.load(f)

    assert state["seen_pages"]["page-42"] == "deadbeef"


def test_mark_seen_preserves_existing_entries(tmp_path):
    state_file = str(tmp_path / "state.json")
    poller = Poller(notion_client=None, state_file=state_file)

    poller.mark_seen("page-1", "hash1")
    poller.mark_seen("page-2", "hash2")

    with open(state_file) as f:
        state = json.load(f)

    assert state["seen_pages"]["page-1"] == "hash1"
    assert state["seen_pages"]["page-2"] == "hash2"


def test_mark_seen_updates_existing_hash(tmp_path):
    state_file = str(tmp_path / "state.json")
    poller = Poller(notion_client=None, state_file=state_file)

    poller.mark_seen("page-1", "old_hash")
    poller.mark_seen("page-1", "new_hash")

    with open(state_file) as f:
        state = json.load(f)

    assert state["seen_pages"]["page-1"] == "new_hash"


def test_mark_seen_creates_state_file_if_missing(tmp_path):
    state_file = str(tmp_path / "state.json")
    assert not os.path.exists(state_file)

    poller = Poller(notion_client=None, state_file=state_file)
    poller.mark_seen("p1", "h1")

    assert os.path.exists(state_file)


# ---------------------------------------------------------------------------
# state.json structure
# ---------------------------------------------------------------------------

def test_state_file_has_correct_structure(tmp_path):
    state_file = str(tmp_path / "state.json")
    poller = Poller(notion_client=None, state_file=state_file)
    poller.mark_seen("p1", "h1")

    with open(state_file) as f:
        state = json.load(f)

    assert "seen_pages" in state
    assert "active_runs" in state
