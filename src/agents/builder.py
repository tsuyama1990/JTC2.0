import logging
from typing import Any

from src.agents.base import BaseAgent
from src.core.config import get_settings
from src.core.interfaces import LLMInterface
from src.domain_models.agent_prompt import AgentPromptSpec
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


class BuilderAgent(BaseAgent):
    """
    Agent responsible for output generation (Phase 5).
    Role Change: Generates the ultimate requirements definition document AgentPromptSpec
    that is applicable to any AI coding tool.
    """

    def __init__(self, llm: LLMInterface) -> None:
        self.llm = llm
        self.settings = get_settings()

    def generate_agent_prompt_spec(self, state: GlobalState) -> dict[str, Any]:
        """Generate Agent Prompt Spec."""
        if not state.sitemap_and_story:
            logger.warning("Missing sitemap for Agent Prompt Spec.")
            return {}

        system_message = "You are a Senior Technical Lead. Generate a perfect AgentPromptSpec markdown specification for AI coding tools."
        prompt = f"Core Story: {state.sitemap_and_story.core_story.model_dump()}\n\nGenerate Agent Prompt Spec:"
        try:
            result = self.llm.generate_structured(
                prompt, AgentPromptSpec, system_message=system_message
            )
            if isinstance(result, AgentPromptSpec):
                return {"agent_prompt_spec": result}
        except Exception:
            logger.exception("Failed to generate Agent Prompt Spec")
        return {}

    def run(self, state: GlobalState) -> dict[str, Any]:
        """
        Execute MVP Generation for the selected feature.
        """
        return self.generate_agent_prompt_spec(state)
