"""Custom exception classes for the Notion Spec-to-Ship Pipeline."""


class EmptyIdeaError(ValueError):
    """Raised when the Idea_Page content is empty or fewer than 10 characters."""


class SpecGenerationError(RuntimeError):
    """Raised when the Spec Generator fails after exhausting all retries."""


class NotionWriteError(RuntimeError):
    """Raised when a Notion MCP write call fails after exhausting all retries."""


class TaskExecutionError(RuntimeError):
    """Raised when the Coding Agent fails to execute a task."""


class StatusSyncError(RuntimeError):
    """Raised when a status sync write to Notion fails after exhausting all retries."""


class MCPConnectionError(RuntimeError):
    """Raised when the Notion MCP connection cannot be established at startup."""
