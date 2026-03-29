"""Retry decorator with exponential backoff for external calls."""

import time
import functools
from typing import Callable, Any


def retry(max_attempts: int = 3, backoff_base: float = 1.0, backoff_factor: float = 2.0):
    """Decorator factory that retries a function with exponential backoff.

    On each failure, sleeps for backoff_base * (backoff_factor ** attempt) seconds.
    After max_attempts exhausted, re-raises the last exception.

    Args:
        max_attempts: Maximum number of attempts before giving up.
        backoff_base: Base sleep duration in seconds.
        backoff_factor: Multiplier applied per attempt (exponential growth).
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None
            for attempt in range(max_attempts):
                try:
                    return fn(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    if attempt < max_attempts - 1:
                        sleep_time = backoff_base * (backoff_factor ** attempt)
                        time.sleep(sleep_time)
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator
