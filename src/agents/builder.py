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
    Agent responsible for generating the final requirements definition document.
    Loads contexts generated so far and outputs an AgentPromptSpec using structured outputs.
    """

    def __init__(self, llm: ChatOpenAI) -> None:
        self.llm = llm
        self.settings = get_settings()

    def generate_agent_prompt_spec(self, state: GlobalState) -> dict[str, Any]:
        """Generate Agent Prompt Spec."""
        if not state.sitemap_and_story:
            logger.warning("Missing sitemap for Agent Prompt Spec generation.")
            return {}

        context_str = f"Core Story: {state.sitemap_and_story.core_story.model_dump()}\n"
        if state.value_proposition:
            context_str += f"Value Proposition: {state.value_proposition.model_dump()}\n"
        if state.mental_model:
            context_str += f"Mental Model: {state.mental_model.model_dump()}\n"
        if state.customer_journey:
            context_str += f"Customer Journey: {state.customer_journey.model_dump()}\n"
        if state.sitemap_and_story:
            context_str += f"Sitemap: {state.sitemap_and_story.model_dump()}\n"
        if state.debate_history:
            context_str += (
                f"3H Review History: {[msg.model_dump() for msg in state.debate_history]}\n"
            )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a Senior Technical Lead. Loads all contexts generated so far (VPC, Mental Model, Journey, Story, Sitemap, 3H Review results) as an integrated prerequisite. After applying 'subtractive thinking' (removing unnecessary features that do not directly solve the user's Pain), generate a perfect AgentPromptSpec markdown specification for AI coding tools.",
                ),
                (
                    "user",
                    f"{context_str}\n\nGenerate Agent Prompt Spec:",
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
        Run method required by BaseAgent.
        """
        return self.generate_agent_prompt_spec(state)
