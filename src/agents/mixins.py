import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class RateLimitMixin:
    """Mixin for API rate limiting."""

    def __init__(self) -> None:
        self._last_request_time: float = 0.0
        self._min_request_interval: float = 1.0

    def _rate_limit_wait(self) -> None:
        """Enforce rate limiting for API calls."""
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()


class ErrorHandlingMixin:
    """Mixin for consistent error logging."""

    def _log_error(self, method_name: str, error: Exception) -> None:
        logger.error(f"Error in {method_name}: {error}", exc_info=True)

    def _safe_execute(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self._log_error(func.__name__, e)
            return None
