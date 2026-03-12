import logging
from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from src.agents.base import BaseAgent
from src.core.config import get_settings
from src.core.interfaces import ILLMClient
from src.domain_models.agent_prompt_spec import AgentPromptSpec
from src.domain_models.experiment_plan import ExperimentPlan
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


class BuilderAgent(BaseAgent):
    """
    Agent responsible for output generation (Phase 5 & 6).
    It generates the AgentPromptSpec and ExperimentPlan.
    """

    def __init__(self, llm: ILLMClient) -> None:
        self.llm = llm
        self.settings = get_settings()

    def generate_spec(self, state: GlobalState) -> dict[str, Any]:
        """
        Generate AgentPromptSpec using LLM with structured output.
        """
        if not state.sitemap_and_story:
            logger.warning("No sitemap available for Spec Generation.")
            return {}

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert product builder. Use the provided context to generate the ultimate AgentPromptSpec.",
                ),
                (
                    "user",
                    f"Sitemap & Story: {state.sitemap_and_story.model_dump_json() if state.sitemap_and_story else ''}\n"
                    f"Mental Model: {state.mental_model_diagram.model_dump_json() if state.mental_model_diagram else ''}\n"
                    f"VPC: {state.value_proposition_canvas.model_dump_json() if state.value_proposition_canvas else ''}\n"
                    "Generate AgentPromptSpec:",
                ),
            ]
        )
        try:
            structured_llm = self.llm.with_structured_output(AgentPromptSpec)
            messages = prompt.format_messages()
            result = structured_llm.invoke(messages)
            if isinstance(result, AgentPromptSpec):
                return {"agent_prompt_spec": result}
        except Exception:
            logger.exception("Failed to create AgentPromptSpec")

        return {}

    def generate_experiment_plan(self, state: GlobalState) -> dict[str, Any]:
        """
        Generate ExperimentPlan using LLM with structured output.
        """
        if not state.agent_prompt_spec:
            logger.warning("No AgentPromptSpec available for Experiment Plan Generation.")
            return {}

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert product growth manager. Use the provided context to generate an Experiment Plan.",
                ),
                (
                    "user",
                    f"Agent Prompt Spec: {state.agent_prompt_spec.model_dump_json() if state.agent_prompt_spec else ''}\n"
                    "Generate ExperimentPlan:",
                ),
            ]
        )
        try:
            structured_llm = self.llm.with_structured_output(ExperimentPlan)
            messages = prompt.format_messages()
            result = structured_llm.invoke(messages)
            if isinstance(result, ExperimentPlan):
                return {"experiment_plan": result}
        except Exception:
            logger.exception("Failed to create ExperimentPlan")

        return {}

    def run(self, state: GlobalState) -> dict[str, Any]:
        """
        Run method. Delegates to generate_spec (default behavior).
        """
        return self.generate_spec(state)
