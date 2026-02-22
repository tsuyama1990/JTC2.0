from abc import ABC, abstractmethod
from typing import Any

from src.domain_models.state import GlobalState


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    @abstractmethod
    def run(self, state: GlobalState) -> dict[str, Any]:
        """
        Run the agent logic.

        Args:
            state: The current global state.

        Returns:
            A dictionary containing state updates.
        """
