import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class RetryHandler:
    """Handles execution of logic with retry capabilities."""

    @staticmethod
    def execute_with_retry(
        func: Callable[[], Any],
        max_attempts: int = 3,
        error_msg: str = "Error executing operation",
    ) -> Any:
        """Execute a function with standardized retry handling."""
        for attempt in range(max_attempts):
            try:
                return func()
            except PermissionError:
                logger.exception(f"Permission denied: {error_msg}")
                break  # No point retrying permission error
            except OSError:
                if attempt < max_attempts - 1:
                    logger.warning(
                        f"OS error: {error_msg}, retrying... ({attempt + 1}/{max_attempts})"
                    )
                    continue
                logger.exception(f"OS error: {error_msg} after {max_attempts} attempts")
            except Exception:
                logger.exception(f"Unexpected error: {error_msg}")
                break
        return None
