from abc import ABC, abstractmethod
from typing import Any

from src.domain_models.state import GlobalState


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the JTC 2.0 system.

    All agents must implement the `run` method which takes a GlobalState
    and returns state updates.
    """

    @abstractmethod
    def run(self, state: GlobalState) -> dict[str, Any]:
        """
        Run the agent logic.

        This method is the entry point for the agent's workflow node.

        Args:
            state: The current global state of the application.

        Returns:
            A dictionary containing key-value pairs to update the global state.
            Example: {"generated_ideas": [Idea1, Idea2]}
        """
