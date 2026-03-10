import logging
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
    jitter_pct_min: float = Field(default=0.0, ge=0.0, le=1.0)
    jitter_pct_max: float = Field(default=0.5, ge=0.0, le=1.0)
    retryable_exceptions: tuple[type[Exception], ...] = Field(default=(OSError,))
    fatal_exceptions: tuple[type[Exception], ...] = Field(default=(PermissionError,))

    model_config = {"arbitrary_types_allowed": True}


class RetryHandlerConfig:
    """Encapsulates dependencies for the RetryHandler to allow deterministic testing."""
    def __init__(
        self,
        strategy: RetryStrategy | None = None,
        logger_override: logging.Logger | None = None,
        sleep_func: Callable[[float], None] | None = None,
        random_uniform_func: Callable[[float, float], float] | None = None
    ) -> None:
        import random
        import time
        self.strategy = strategy or RetryStrategy()
        self.logger = logger_override or logger
        self.sleep = sleep_func or time.sleep
        self.random_uniform = random_uniform_func or random.uniform


class RetryHandler:
    """Handles configurable retry logic for synchronous operations."""

    def __init__(self, config: RetryHandlerConfig | None = None) -> None:
        self.config = config or RetryHandlerConfig()

    def execute_with_retry(
        self,
        func: Callable[[], T],
        error_msg: str = "Operation failed",
    ) -> T | None:
        """
        Execute a function with retry logic.
        """
        strategy = self.config.strategy
        for attempt in range(strategy.max_attempts):
            try:
                return func()
            except strategy.fatal_exceptions:
                self.config.logger.exception(f"{error_msg}: Fatal error encountered")
                break
            except strategy.retryable_exceptions as e:
                if attempt < strategy.max_attempts - 1:
                    self.config.logger.warning(
                        f"{error_msg}, retrying... ({attempt + 1}/{strategy.max_attempts}). Error: {e}"
                    )

                    # Exponential backoff with configurable jitter
                    base_delay = 1.0 * (2**attempt)
                    jitter_pct = self.config.random_uniform(strategy.jitter_pct_min, strategy.jitter_pct_max)
                    jitter = jitter_pct * base_delay
                    self.config.sleep(base_delay + jitter)
                    continue
                self.config.logger.exception(f"{error_msg} after {strategy.max_attempts} attempts")
            except Exception:
                self.config.logger.exception(f"Unexpected error during {error_msg}")
                break
        return None


class AsyncRetryHandlerConfig:
    """Encapsulates dependencies for the AsyncRetryHandler to allow deterministic testing."""
    def __init__(
        self,
        strategy: RetryStrategy | None = None,
        logger_override: logging.Logger | None = None,
        async_sleep_func: Callable[[float], Awaitable[None]] | None = None,
        random_uniform_func: Callable[[float, float], float] | None = None
    ) -> None:
        import asyncio
        import random
        self.strategy = strategy or RetryStrategy()
        self.logger = logger_override or logger
        self.async_sleep = async_sleep_func or asyncio.sleep
        self.random_uniform = random_uniform_func or random.uniform


class AsyncRetryHandler:
    """Handles configurable retry logic for asynchronous operations."""

    def __init__(self, config: AsyncRetryHandlerConfig | None = None) -> None:
        self.config = config or AsyncRetryHandlerConfig()

    async def execute_with_retry_async(
        self,
        func: Callable[[], Awaitable[T]],
        error_msg: str = "Operation failed",
    ) -> T | None:
        """
        Execute an async function with retry logic and exponential backoff.
        """
        strategy = self.config.strategy
        for attempt in range(strategy.max_attempts):
            try:
                return await func()
            except strategy.fatal_exceptions:
                self.config.logger.exception(f"{error_msg}: Fatal error encountered")
                break
            except strategy.retryable_exceptions as e:
                if attempt < strategy.max_attempts - 1:
                    self.config.logger.warning(
                        f"{error_msg}, retrying... ({attempt + 1}/{strategy.max_attempts}). Error: {e}"
                    )

                    # Exponential backoff with secure jitter
                    base_delay = 1.0 * (2**attempt)
                    jitter_pct = self.config.random_uniform(strategy.jitter_pct_min, strategy.jitter_pct_max)
                    jitter = jitter_pct * base_delay
                    await self.config.async_sleep(base_delay + jitter)
                    continue
                self.config.logger.exception(f"{error_msg} after {strategy.max_attempts} attempts")
            except Exception:
                self.config.logger.exception(f"Unexpected error during {error_msg}")
                break
        return None
