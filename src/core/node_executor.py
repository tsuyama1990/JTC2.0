import functools
import logging
from collections.abc import Callable
from typing import Any

from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


class NodeExecutor:
    """Handles execution of node logic with consistent error handling."""

    @staticmethod
    def execute(
        func: Callable[[GlobalState], dict[str, Any]],
        state: GlobalState,
        error_msg: str = "Error executing node",
    ) -> dict[str, Any]:
        """Execute a function with standardized error handling."""
        try:
            return func(state)
        except Exception as e:
            logger.exception(f"{error_msg}: {e.__class__.__name__}")
            return {
                "_node_error": True,
                "messages": [*state.messages, f"System encountered an error: {e}"],
            }


def safe_node(
    error_msg: str = "Error in graph node",
) -> Callable[[Callable[..., Any]], Callable[..., dict[str, Any]]]:
    """Decorator to wrap graph nodes with consistent error handling."""

    def decorator(func: Callable[..., Any]) -> Callable[..., dict[str, Any]]:
        @functools.wraps(func)
        def wrapper(state: GlobalState) -> dict[str, Any]:
            return NodeExecutor.execute(func, state, error_msg)

        return wrapper

    return decorator
