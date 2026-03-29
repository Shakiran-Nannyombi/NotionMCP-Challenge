"""Data models for the Notion Spec-to-Ship Pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class RunStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"


class TaskStatus(str, Enum):
    TODO = "To Do"
    IN_PROGRESS = "In Progress"
    DONE = "Done"
    FAILED = "Failed"


@dataclass
class Requirement:
    id: str                          # e.g. "R1"
    title: str
    user_story: str
    acceptance_criteria: list[str]   # EARS-formatted strings


@dataclass
class Task:
    order: int
    title: str
    description: str
    acceptance_criteria: str


@dataclass
class Spec:
    introduction: str
    requirements: list[Requirement]
    tasks: list[Task]


@dataclass
class TaskResult:
    success: bool
    output: str
    error: str | None = None


@dataclass
class TaskRecord:
    order: int
    title: str
    notion_page_id: str
    status: TaskStatus = TaskStatus.TODO
    error: str | None = None


@dataclass
class PipelineRun:
    run_id: str                      # UUID
    idea_page_id: str
    status: RunStatus = RunStatus.PENDING
    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: datetime | None = None
    tasks: list[TaskRecord] = field(default_factory=list)
