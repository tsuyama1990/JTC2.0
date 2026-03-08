import logging
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.agents.base import BaseAgent
from src.core.config import get_settings
from src.domain_models.agent_prompt import AgentPromptSpec
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


class BuilderAgent(BaseAgent):
    """
    Agent responsible for output generation (Phase 5).
    Role Change: Generates the ultimate requirements definition document AgentPromptSpec
    that is applicable to any AI coding tool.
    """

    def __init__(self, llm: ChatOpenAI) -> None:
        self.llm = llm
        self.settings = get_settings()

    def generate_agent_prompt_spec(self, state: GlobalState) -> dict[str, Any]:
        """Generate Agent Prompt Spec."""
        if not state.sitemap_and_story:
            logger.warning("Missing sitemap for Agent Prompt Spec.")
            return {}

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a Senior Technical Lead. Generate a perfect AgentPromptSpec markdown specification for AI coding tools.",
                ),
                (
                    "user",
                    f"Core Story: {state.sitemap_and_story.core_story.model_dump()}\n\nGenerate Agent Prompt Spec:",
                ),
            ]
        )
        chain = prompt | self.llm.with_structured_output(AgentPromptSpec)
        try:
            result = chain.invoke({})
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
