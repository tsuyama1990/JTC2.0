import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T", bound=Any)

logger = logging.getLogger(__name__)


class RetryStrategy(BaseModel):
    max_attempts: int = Field(default=3, ge=1)
    retryable_exceptions: tuple[type[Exception], ...] = Field(default=(OSError,))
    fatal_exceptions: tuple[type[Exception], ...] = Field(default=(PermissionError,))

    model_config = {"arbitrary_types_allowed": True}


class RetryHandler:
    """Handles configurable retry logic for synchronous operations."""

    def __init__(self, strategy: RetryStrategy | None = None) -> None:
        self.strategy = strategy or RetryStrategy()

    def execute_with_retry(
        self,
        func: Callable[[], T],
        error_msg: str = "Operation failed",
    ) -> T | None:
        """
        Execute a function with retry logic.
        """
        for attempt in range(self.strategy.max_attempts):
            try:
                return func()
            except self.strategy.fatal_exceptions:
                logger.exception(f"{error_msg}: Fatal error encountered")
                break
            except self.strategy.retryable_exceptions as e:
                if attempt < self.strategy.max_attempts - 1:
                    logger.warning(
                        f"{error_msg}, retrying... ({attempt + 1}/{self.strategy.max_attempts}). Error: {e}"
                    )
                    import secrets

                    # Exponential backoff with secure jitter
                    base_delay = 1.0 * (2**attempt)
                    # randbelow requires an int, we use it to get a percentage
                    jitter_pct = secrets.randbelow(51) / 100.0  # 0 to 50%
                    jitter = jitter_pct * base_delay
                    time.sleep(base_delay + jitter)
                    continue
                logger.exception(f"{error_msg} after {self.strategy.max_attempts} attempts")
            except Exception:
                logger.exception(f"Unexpected error during {error_msg}")
                break
        return None


class AsyncRetryHandler:
    """Handles configurable retry logic for asynchronous operations."""

    def __init__(self, strategy: RetryStrategy | None = None) -> None:
        self.strategy = strategy or RetryStrategy()

    async def execute_with_retry_async(
        self,
        func: Callable[[], Awaitable[T]],
        error_msg: str = "Operation failed",
    ) -> T | None:
        """
        Execute an async function with retry logic and exponential backoff.
        """
        for attempt in range(self.strategy.max_attempts):
            try:
                return await func()
            except self.strategy.fatal_exceptions:
                logger.exception(f"{error_msg}: Fatal error encountered")
                break
            except self.strategy.retryable_exceptions as e:
                if attempt < self.strategy.max_attempts - 1:
                    logger.warning(
                        f"{error_msg}, retrying... ({attempt + 1}/{self.strategy.max_attempts}). Error: {e}"
                    )
                    import secrets

                    # Exponential backoff with secure jitter
                    base_delay = 1.0 * (2**attempt)
                    jitter_pct = secrets.randbelow(51) / 100.0  # 0 to 50%
                    jitter = jitter_pct * base_delay
                    await asyncio.sleep(base_delay + jitter)
                    continue
                logger.exception(f"{error_msg} after {self.strategy.max_attempts} attempts")
            except Exception:
                logger.exception(f"Unexpected error during {error_msg}")
                break
        return None
