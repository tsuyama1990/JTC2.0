import logging
from collections.abc import Callable
from typing import Any

from src.core.config import Settings
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


class NodeExecutor:
    """Executes a graph node with consistent error handling and injected dependencies."""

    def __init__(self, settings: Settings | None = None, **dependencies: Any) -> None:
        self.settings = settings
        self.dependencies = dependencies

    def execute(
        self,
        func: Callable[..., dict[str, Any]],
        state: GlobalState,
        error_msg: str = "Error in graph node",
    ) -> dict[str, Any]:
        """
        Execute the given pure node function with standard error handling.
        Injects dependencies into the function.

        Args:
            func: The pure node function to execute.
            state: The current graph state.
            error_msg: The custom error message to log on exception.

        Returns:
            A state update dictionary, empty if an error occurred.
        """
        try:
            return func(state, **self.dependencies)
        except Exception:
            logger.exception(error_msg)
            return {}
