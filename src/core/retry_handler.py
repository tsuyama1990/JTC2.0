import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T", bound=Any)


class RetryStrategy(BaseModel):
    max_attempts: int = Field(default=3, ge=1)
    retryable_exceptions: tuple[type[Exception], ...] = Field(default=(OSError,))
    fatal_exceptions: tuple[type[Exception], ...] = Field(default=(PermissionError,))

    model_config = {"arbitrary_types_allowed": True}


class RetryHandlerConfig:
    def __init__(
        self,
        logger: logging.Logger | None = None,
        random_func: "Callable[[int], int] | None" = None,
    ) -> None:
        self.logger = logger or logging.getLogger(__name__)
        if random_func is None:
            import secrets
            import typing

            self.random_func = typing.cast("Callable[[int], int]", secrets.randbelow)
        else:
            self.random_func = random_func


class RetryHandler:
    """Handles configurable retry logic for synchronous operations."""

    def __init__(
        self, strategy: RetryStrategy | None = None, config: RetryHandlerConfig | None = None
    ) -> None:
        self.strategy = strategy or RetryStrategy()
        self.config = config or RetryHandlerConfig()

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
                self.config.logger.exception(f"{error_msg}: Fatal error encountered")
                break
            except self.strategy.retryable_exceptions as e:
                if attempt < self.strategy.max_attempts - 1:
                    self.config.logger.warning(
                        f"{error_msg}, retrying... ({attempt + 1}/{self.strategy.max_attempts}). Error: {e}"
                    )
                    # Exponential backoff with secure jitter
                    base_delay = 1.0 * (2**attempt)
                    jitter_pct = self.config.random_func(51) / 100.0  # 0 to 50%
                    jitter = jitter_pct * base_delay
                    time.sleep(base_delay + jitter)
                    continue
                self.config.logger.exception(
                    f"{error_msg} after {self.strategy.max_attempts} attempts"
                )
            except Exception:
                self.config.logger.exception(f"Unexpected error during {error_msg}")
                break
        return None


class AsyncRetryHandler:
    """Handles configurable retry logic for asynchronous operations."""

    def __init__(
        self, strategy: RetryStrategy | None = None, config: RetryHandlerConfig | None = None
    ) -> None:
        self.strategy = strategy or RetryStrategy()
        self.config = config or RetryHandlerConfig()

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
                self.config.logger.exception(f"{error_msg}: Fatal error encountered")
                break
            except self.strategy.retryable_exceptions as e:
                if attempt < self.strategy.max_attempts - 1:
                    self.config.logger.warning(
                        f"{error_msg}, retrying... ({attempt + 1}/{self.strategy.max_attempts}). Error: {e}"
                    )
                    # Exponential backoff with secure jitter
                    base_delay = 1.0 * (2**attempt)
                    jitter_pct = self.config.random_func(51) / 100.0  # 0 to 50%
                    jitter = jitter_pct * base_delay
                    await asyncio.sleep(base_delay + jitter)
                    continue
                self.config.logger.exception(
                    f"{error_msg} after {self.strategy.max_attempts} attempts"
                )
            except Exception:
                self.config.logger.exception(f"Unexpected error during {error_msg}")
                break
        return None
