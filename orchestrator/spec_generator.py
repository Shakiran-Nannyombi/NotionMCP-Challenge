"""Spec Generator — calls an LLM to produce a structured Spec from raw idea text."""

from __future__ import annotations

import json
import time
from typing import Any, Protocol

from orchestrator.errors import SpecGenerationError
from orchestrator.models import Requirement, Spec, Task


_SYSTEM_PROMPT = """\
You are a software specification assistant. Given a rough idea description, produce a
structured software specification as a single JSON object — no markdown, no prose, ONLY
the JSON object.

The JSON must conform exactly to this schema:

{
  "introduction": "<one-paragraph summary of the project>",
  "requirements": [
    {
      "id": "R1",
      "title": "<short requirement title>",
      "user_story": "<As a ... I want ... so that ...>",
      "acceptance_criteria": [
        "<EARS-formatted criterion — must start with WHEN, IF, WHILE, WHERE, or THE SYSTEM SHALL>"
      ]
    }
  ],
  "tasks": [
    {
      "order": 1,
      "title": "<task title>",
      "description": "<detailed task description>",
      "acceptance_criteria": "<single EARS-formatted criterion>"
    }
  ]
}

Rules:
- Every acceptance_criteria string MUST begin with one of: WHEN, IF, WHILE, WHERE, THE SYSTEM SHALL
- Include at least one Requirement and at least one Task
- The introduction must be non-empty
- Output ONLY the JSON object — no code fences, no extra text
"""


class LLMClient(Protocol):
    """Interface expected by SpecGenerator for the underlying LLM client."""

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        timeout: float,
    ) -> str:
        """Return the model's text response."""
        ...


def _parse_spec(raw: str) -> Spec:
    """Parse a JSON string into a Spec dataclass. Raises ValueError on any issue."""
    # Strip potential markdown code fences if the model ignores instructions
    text = raw.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # drop first and last fence lines
        text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

    data: Any = json.loads(text)

    if not isinstance(data, dict):
        raise ValueError("Top-level JSON value must be an object")

    introduction: str = data.get("introduction", "")
    if not isinstance(introduction, str) or not introduction.strip():
        raise ValueError("'introduction' must be a non-empty string")

    raw_reqs = data.get("requirements")
    if not isinstance(raw_reqs, list) or len(raw_reqs) == 0:
        raise ValueError("'requirements' must be a non-empty list")

    requirements: list[Requirement] = []
    for i, r in enumerate(raw_reqs):
        if not isinstance(r, dict):
            raise ValueError(f"requirements[{i}] must be an object")
        req_id = r.get("id", "")
        title = r.get("title", "")
        user_story = r.get("user_story", "")
        ac = r.get("acceptance_criteria", [])
        if not isinstance(req_id, str) or not req_id.strip():
            raise ValueError(f"requirements[{i}].id must be a non-empty string")
        if not isinstance(title, str) or not title.strip():
            raise ValueError(f"requirements[{i}].title must be a non-empty string")
        if not isinstance(user_story, str):
            raise ValueError(f"requirements[{i}].user_story must be a string")
        if not isinstance(ac, list) or len(ac) == 0:
            raise ValueError(f"requirements[{i}].acceptance_criteria must be a non-empty list")
        requirements.append(
            Requirement(
                id=req_id,
                title=title,
                user_story=user_story,
                acceptance_criteria=[str(c) for c in ac],
            )
        )

    raw_tasks = data.get("tasks")
    if not isinstance(raw_tasks, list) or len(raw_tasks) == 0:
        raise ValueError("'tasks' must be a non-empty list")

    tasks: list[Task] = []
    for i, t in enumerate(raw_tasks):
        if not isinstance(t, dict):
            raise ValueError(f"tasks[{i}] must be an object")
        order = t.get("order")
        title = t.get("title", "")
        description = t.get("description", "")
        ac = t.get("acceptance_criteria", "")
        if not isinstance(order, int):
            raise ValueError(f"tasks[{i}].order must be an integer")
        if not isinstance(title, str) or not title.strip():
            raise ValueError(f"tasks[{i}].title must be a non-empty string")
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"tasks[{i}].description must be a non-empty string")
        if not isinstance(ac, str) or not ac.strip():
            raise ValueError(f"tasks[{i}].acceptance_criteria must be a non-empty string")
        tasks.append(
            Task(
                order=order,
                title=title,
                description=description,
                acceptance_criteria=ac,
            )
        )

    return Spec(introduction=introduction, requirements=requirements, tasks=tasks)


class SpecGenerator:
    """Generates a structured Spec from raw idea text via an LLM.

    Args:
        llm_client: An object with a ``complete(system_prompt, user_prompt,
            temperature, timeout)`` method that returns a string.
    """

    _MAX_ATTEMPTS = 3
    _TEMPERATURE = 0.2
    _TIMEOUT = 120.0
    _BACKOFF_BASE = 1.0
    _BACKOFF_FACTOR = 2.0

    def __init__(self, llm_client: LLMClient) -> None:
        self._llm = llm_client

    def generate(self, idea_text: str) -> Spec:
        """Call the LLM and return a validated Spec.

        Retries up to 3 times on LLM failure or malformed JSON.
        Raises SpecGenerationError after all attempts are exhausted.
        """
        last_exc: Exception | None = None

        for attempt in range(self._MAX_ATTEMPTS):
            try:
                raw = self._llm.complete(
                    system_prompt=_SYSTEM_PROMPT,
                    user_prompt=idea_text,
                    temperature=self._TEMPERATURE,
                    timeout=self._TIMEOUT,
                )
                return _parse_spec(raw)
            except Exception as exc:
                last_exc = exc
                if attempt < self._MAX_ATTEMPTS - 1:
                    sleep_time = self._BACKOFF_BASE * (self._BACKOFF_FACTOR ** attempt)
                    time.sleep(sleep_time)

        raise SpecGenerationError(
            f"Spec generation failed after {self._MAX_ATTEMPTS} attempts"
        ) from last_exc
