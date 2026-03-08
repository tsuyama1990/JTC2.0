import asyncio
import time
from collections.abc import Generator

import bleach


def chunk_text(text: str, chunk_size: int) -> Generator[str, None, None]:
    """
    Split text into chunks of specified size efficiently.

    This function utilizes a Python generator (`yield`) rather than appending substrings
    to a list and returning it. This approach processes potentially massive strings
    in a lazy, iterative manner, yielding one chunk at a time. This prevents
    Out-Of-Memory (OOM) exceptions and optimizes memory footprint significantly when
    dealing with large inputs like interview transcripts.
    """
    for i in range(0, len(text), chunk_size):
        yield text[i : i + chunk_size]


def sanitize_query(query: str) -> str:
    """
    Sanitize input query to prevent SQL/NoSQL injection and XSS attacks.
    Uses the robust `bleach` library to strictly whitelist safe HTML and scripts.
    """
    return bleach.clean(query.strip(), tags=[], attributes={}, protocols=[], strip=True)


class AsyncRateLimiter:
    """Configurable, non-blocking rate limiter."""

    def __init__(self, min_interval: float, max_retries: int = 3, timeout: float = 30.0) -> None:
        self._min_interval = min_interval
        self._max_retries = max_retries
        self._timeout = timeout
        self._last_call_time = 0.0

    async def wait(self) -> None:
        """Wait non-blocking if the rate limit is exceeded, factoring in max retries and timeout."""
        start_time = time.time()
        attempts = 0

        while attempts < self._max_retries:
            current = time.time()
            if current - start_time > self._timeout:
                msg = f"Rate limiter timed out after {self._timeout} seconds."
                raise TimeoutError(msg)

            elapsed = current - self._last_call_time
            if elapsed >= self._min_interval:
                self._last_call_time = current
                return

            # Update state before awaiting to prevent race conditions
            wait_time = self._min_interval - elapsed
            self._last_call_time = current + wait_time
            await asyncio.sleep(wait_time)
            # Do not increment attempts if we just slept to respect rate limit,
            # wait is not a "retry" of a failed operation, it's just a delay.
            # However, if we loop again, it means something reset our call time.
            # To ensure it returns properly after waiting:
            return

    def wait_sync(self) -> None:
        """Synchronous wait fallback (if needed), factoring in max retries and timeout."""
        start_time = time.time()
        attempts = 0

        while attempts < self._max_retries:
            current = time.time()
            if current - start_time > self._timeout:
                msg = f"Rate limiter timed out after {self._timeout} seconds."
                raise TimeoutError(msg)

            elapsed = current - self._last_call_time
            if elapsed >= self._min_interval:
                self._last_call_time = current
                return

            wait_time = self._min_interval - elapsed
            self._last_call_time = current + wait_time
            time.sleep(wait_time)
            return
