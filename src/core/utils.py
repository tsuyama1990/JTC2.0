import asyncio
import threading
import time
from collections.abc import Generator
from pathlib import Path

import bleach

from src.core.config import Settings, get_settings


def chunk_text(text: str, chunk_size: int) -> Generator[str, None, None]:
    """
    Split text into chunks of specified size efficiently.

    This function utilizes a Python generator (`yield`) rather than appending substrings
    to a list and returning it. This approach processes potentially massive strings
    in a lazy, iterative manner, yielding one chunk at a time. This prevents
    Out-Of-Memory (OOM) exceptions and optimizes memory footprint significantly when
    dealing with large inputs like interview transcripts.
    """
    if chunk_size <= 0:
        msg = "chunk_size must be greater than 0"
        raise ValueError(msg)

    for i in range(0, len(text), chunk_size):
        yield text[i : i + chunk_size]


def strip_html_tags(query: str) -> str:
    """
    Strips ALL HTML tags and scripts from the input string using bleach.

    WARNING: This function does NOT prevent SQL injection or Command injection.
    It is NOT intended for security purposes. For database operations, always
    use parameterized queries (e.g. via SQLAlchemy).
    """
    if not isinstance(query, str):
        msg = "Input query must be a string."
        raise TypeError(msg)

    # Strip HTML using comprehensive library
    stripped: str = bleach.clean(query.strip(), tags=[], attributes={}, protocols=[], strip=True)

    return stripped.strip()


class AsyncRateLimiter:
    """Configurable, non-blocking rate limiter."""

    def __init__(
        self,
        min_interval: float,
        settings: Settings | None = None,
        max_retries: int | None = None,
        timeout: float | None = None,
    ) -> None:
        sys_settings = settings or get_settings()
        self._min_interval = min_interval
        self._max_retries = (
            max_retries
            if max_retries is not None
            else sys_settings.resiliency.circuit_breaker_fail_max
        )
        self._timeout = timeout if timeout is not None else sys_settings.rag.query_timeout
        self._last_call_time = 0.0
        self._async_lock: asyncio.Lock | None = None
        self._sync_lock = threading.Lock()

    async def wait(self) -> None:
        """Wait non-blocking if the rate limit is exceeded, factoring in max retries and timeout."""
        if self._async_lock is None:
            self._async_lock = asyncio.Lock()

        async with self._async_lock:
            current = time.time()

            elapsed = current - self._last_call_time
            if elapsed >= self._min_interval:
                self._last_call_time = current
                return

            # Update state before awaiting to prevent race conditions
            wait_time = self._min_interval - elapsed
            if wait_time > self._timeout:
                msg = f"Rate limiter wait time ({wait_time}s) exceeds timeout of {self._timeout} seconds."
                raise TimeoutError(msg)

            self._last_call_time = current + wait_time

        # Sleep outside the lock so other tasks don't block on our sleep
        await asyncio.sleep(wait_time)

    def wait_sync(self) -> None:
        """Synchronous wait fallback (if needed), factoring in max retries and timeout."""
        with self._sync_lock:
            current = time.time()

            elapsed = current - self._last_call_time
            if elapsed >= self._min_interval:
                self._last_call_time = current
                return

            wait_time = self._min_interval - elapsed
            if wait_time > self._timeout:
                msg = f"Rate limiter wait time ({wait_time}s) exceeds timeout of {self._timeout} seconds."
                raise TimeoutError(msg)

            self._last_call_time = current + wait_time

        # Sleep outside the lock so other threads don't block
        time.sleep(wait_time)


def validate_safe_path(
    path: str | Path, allowed_paths: list[str] | list[Path] | None = None
) -> Path:
    """
    Validate path to prevent traversal using absolute paths and containment.
    """
    from src.core.exceptions import ConfigurationError

    try:
        cwd = Path.cwd().resolve(strict=True)
        # Use strict=False to handle paths that don't exist yet
        p = Path(path).resolve(strict=False)

        # If allowed_paths is None, default to cwd
        if allowed_paths is None:
            allowed_parents = [cwd]
        else:
            # We want to check against the parents given in allowed_paths, relative to cwd
            allowed_parents = [
                (cwd / Path(allowed_path)).resolve(strict=False) for allowed_path in allowed_paths
            ]

        # Verify the resolved path strictly starts with the base path
        if not any(str(p).startswith(str(parent)) for parent in allowed_parents):
            msg = f"Path traversal detected: {p}"
            # Don't import logger here to avoid circular imports or just use ValueError/ConfigurationError
            raise ConfigurationError(msg)

        # Additional check for symlinks if we want to be strict, but resolve handles most
        if p.exists() and p.is_symlink():
            msg = f"Symlinks not allowed in paths: {p}"
            raise ConfigurationError(msg)
    except ConfigurationError:
        raise
    except Exception as e:
        msg = f"Invalid path format: {e}"
        raise ConfigurationError(msg) from e
    else:
        return p
