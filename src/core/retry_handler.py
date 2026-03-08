import logging
import threading
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)


class RetryHandler:
    """Handles retry logic for operations."""

    _lock = threading.Lock()

    @staticmethod
    def execute_with_retry(
        func: Callable[[], T],
        max_attempts: int = 3,
        error_msg: str = "Operation failed",
        retryable_exceptions: tuple[type[Exception], ...] = (OSError,),
        fatal_exceptions: tuple[type[Exception], ...] = (PermissionError,),
    ) -> T | None:
        """
        Execute a function with retry logic.

        Args:
            func: The function to execute.
            max_attempts: Maximum number of attempts.
            error_msg: Base error message for logging.
            retryable_exceptions: Exceptions that should trigger a retry.
            fatal_exceptions: Exceptions that should abort retries immediately.

        Returns:
            The result of the function if successful, otherwise None.
        """
        for attempt in range(max_attempts):
            try:
                with RetryHandler._lock:
                    return func()
            except fatal_exceptions:
                logger.exception(f"{error_msg}: Fatal error encountered")
                break
            except retryable_exceptions as e:
                if attempt < max_attempts - 1:
                    logger.warning(
                        f"{error_msg}, retrying... ({attempt + 1}/{max_attempts}). Error: {e}"
                    )
                    # Global coordinated backoff to prevent thundering herd
                    with RetryHandler._lock:
                        time.sleep(1.0 * (attempt + 1))
                    continue
                logger.exception(f"{error_msg} after {max_attempts} attempts")
            except Exception:
                logger.exception(f"Unexpected error during {error_msg}")
                break
        return None
