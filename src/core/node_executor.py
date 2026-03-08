import logging
from collections.abc import Callable
from typing import Any

from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


class NodeExecutor:
    """Executes a graph node with consistent error handling."""

    @staticmethod
    def execute(
        func: Callable[[GlobalState], dict[str, Any]],
        state: GlobalState,
        error_msg: str = "Error in graph node",
    ) -> dict[str, Any]:
        """
        Execute the given node function with standard error handling.

        Args:
            func: The node function to execute.
            state: The current graph state.
            error_msg: The custom error message to log on exception.

        Returns:
            A state update dictionary, empty if an error occurred.
        """
        try:
            return func(state)
        except Exception:
            logger.exception(error_msg)
            return {}
