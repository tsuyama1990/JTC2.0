import asyncio
import time
from collections.abc import Iterator


def chunk_text(text: str, chunk_size: int) -> Iterator[str]:
    """
    Split text into chunks of specified size efficiently.
    Uses generator to avoid loading list of chunks into memory.
    """
    for i in range(0, len(text), chunk_size):
        yield text[i : i + chunk_size]


def sanitize_query(query: str) -> str:
    """
    Sanitize input query to prevent injection or processing issues.
    Efficient implementation using list comprehension.
    """
    chars = [ch for ch in query if (32 <= ord(ch) < 127) or ch in "\t\r\n" or ord(ch) > 127]
    return "".join(chars).strip()


class AsyncRateLimiter:
    """Configurable, non-blocking rate limiter."""

    def __init__(self, min_interval: float) -> None:
        self._min_interval = min_interval
        self._last_call_time = 0.0

    async def wait(self) -> None:
        """Wait non-blocking if the rate limit is exceeded."""
        current = time.time()
        elapsed = current - self._last_call_time
        if elapsed < self._min_interval:
            await asyncio.sleep(self._min_interval - elapsed)
        self._last_call_time = time.time()

    def wait_sync(self) -> None:
        """Synchronous wait fallback (if needed)."""
        current = time.time()
        elapsed = current - self._last_call_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call_time = time.time()
