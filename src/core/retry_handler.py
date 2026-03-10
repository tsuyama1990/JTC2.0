import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T", bound=Any)

logger = logging.getLogger(__name__)


import abc

class IRetryStrategy(abc.ABC):
    @property
    @abc.abstractmethod
    def max_attempts(self) -> int:
        pass

    @property
    @abc.abstractmethod
    def retryable_exceptions(self) -> tuple[type[Exception], ...]:
        pass

    @property
    @abc.abstractmethod
    def fatal_exceptions(self) -> tuple[type[Exception], ...]:
        pass

    @abc.abstractmethod
    def get_delay(self, attempt: int) -> float:
        pass


class ExponentialBackoffStrategy(BaseModel, IRetryStrategy):
    max_attempts_val: int = Field(default=3, ge=1)
    retryable_exceptions_val: tuple[type[Exception], ...] = Field(default=(OSError,))
    fatal_exceptions_val: tuple[type[Exception], ...] = Field(default=(PermissionError,))
    base_delay: float = Field(default=1.0, ge=0.1)
    max_jitter_pct: float = Field(default=0.5, ge=0.0, le=1.0)

    model_config = {"arbitrary_types_allowed": True}

    @property
    def max_attempts(self) -> int:
        return self.max_attempts_val

    @property
    def retryable_exceptions(self) -> tuple[type[Exception], ...]:
        return self.retryable_exceptions_val

    @property
    def fatal_exceptions(self) -> tuple[type[Exception], ...]:
        return self.fatal_exceptions_val

    def get_delay(self, attempt: int) -> float:
        import random
        base_delay = self.base_delay * (2**attempt)
        jitter_pct = random.uniform(0, self.max_jitter_pct)
        return base_delay + (jitter_pct * base_delay)


class RetryHandler:
    """Handles configurable retry logic for synchronous operations."""

    def __init__(self, strategy: IRetryStrategy) -> None:
        self.strategy = strategy

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
                    time.sleep(self.strategy.get_delay(attempt))
                    continue
                logger.exception(f"{error_msg} after {self.strategy.max_attempts} attempts")
            except Exception:
                logger.exception(f"Unexpected error during {error_msg}")
                break
        return None


class AsyncRetryHandler:
    """Handles configurable retry logic for asynchronous operations."""

    def __init__(self, strategy: IRetryStrategy) -> None:
        self.strategy = strategy

    async def execute_with_retry_async(
        self,
        func: Callable[[], Awaitable[T]],
        error_msg: str = "Operation failed",
    ) -> T | None:
        """
        Execute an async function with retry logic and configurable backoff.
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
                    await asyncio.sleep(self.strategy.get_delay(attempt))
                    continue
                logger.exception(f"{error_msg} after {self.strategy.max_attempts} attempts")
            except Exception:
                logger.exception(f"Unexpected error during {error_msg}")
                break
        return None
