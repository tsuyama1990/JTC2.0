import logging
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from tenacity import retry, stop_after_attempt, wait_exponential

from src.agents.base import BaseAgent
from src.core.config import get_settings
from src.core.interfaces import ILLMClient, IStateContext
from src.domain_models.agent_prompt_spec import AgentPromptSpec
from src.domain_models.experiment_plan import ExperimentPlan

logger = logging.getLogger(__name__)

def _raise_invalid_output() -> None:
    msg = "Invalid output"
    raise TypeError(msg)

class BuilderAgent(BaseAgent):
    """
    Agent responsible for output generation (Phase 5 & 6).
    It generates the AgentPromptSpec and ExperimentPlan.
    """

    def __init__(self, llm: ILLMClient) -> None:
        self.llm = llm
        self.settings = get_settings()

    def generate_spec(self, state: IStateContext) -> dict[str, Any]:
        """
        Generate AgentPromptSpec using LLM with structured output.
        """
        if not state.sitemap_and_story:
            logger.warning("No sitemap available for Spec Generation.")
            return {}

        sitemap_json = state.sitemap_and_story.model_dump_json() if state.sitemap_and_story else "{}"
        mental_json = state.mental_model_diagram.model_dump_json() if hasattr(state, "mental_model_diagram") and state.mental_model_diagram else "{}"
        vpc_json = state.value_proposition_canvas.model_dump_json() if hasattr(state, "value_proposition_canvas") and state.value_proposition_canvas else "{}"
        debate = "\n".join(state.debate_history) if hasattr(state, "debate_history") and state.debate_history else ""

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert product builder. Use the provided context to generate the ultimate AgentPromptSpec.\n"
                    "CRITICAL: Apply strict 'subtraction thinking'. Aggressively strip away ANY unnecessary features "
                    "that do not directly solve the core customer pain points identified in the VPC and Mental Model. "
                    "The resulting specification must be minimal, lean, and absolutely focused on the core User Story."
                ),
                (
                    "user",
                    "Sitemap & Story:\n{sitemap}\n"
                    "Mental Model:\n{mental}\n"
                    "VPC:\n{vpc}\n"
                    "Debate History (Feedback):\n{debate}\n"
                    "Generate the most minimal, lean AgentPromptSpec possible:",
                ),
            ]
        )
        try:
            structured_llm = self.llm.with_structured_output(AgentPromptSpec)
            messages = prompt.format_messages(
                sitemap=sitemap_json,
                mental=mental_json,
                vpc=vpc_json,
                debate=debate
            )

            @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
            def _invoke() -> AgentPromptSpec:
                res = structured_llm.invoke(messages)
                if not isinstance(res, AgentPromptSpec):
                    _raise_invalid_output()
                return res  # type: ignore[no-any-return]

            result = _invoke()
            if isinstance(result, AgentPromptSpec):
                return {"agent_prompt_spec": result}
        except Exception:
            logger.exception("Failed to create AgentPromptSpec")

        return {}

    def generate_experiment_plan(self, state: IStateContext) -> dict[str, Any]:
        """
        Generate ExperimentPlan using LLM with structured output.
        """
        if not state.agent_prompt_spec:
            logger.warning("No AgentPromptSpec available for Experiment Plan Generation.")
            return {}

        spec_json = state.agent_prompt_spec.model_dump_json() if state.agent_prompt_spec else "{}"

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert product growth manager. Use the provided context to generate an Experiment Plan.\n"
                    "Focus strictly on validating the absolute core assumptions necessary for PMF using the AARRR framework. "
                    "Apply 'subtraction thinking' to ensure the plan is actionable and not bloated with vanity metrics."
                ),
                (
                    "user",
                    "Agent Prompt Spec:\n{spec}\n"
                    "Generate ExperimentPlan:",
                ),
            ]
        )
        try:
            structured_llm = self.llm.with_structured_output(ExperimentPlan)
            messages = prompt.format_messages(spec=spec_json)

            @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
            def _invoke() -> ExperimentPlan:
                res = structured_llm.invoke(messages)
                if not isinstance(res, ExperimentPlan):
                    _raise_invalid_output()
                return res  # type: ignore[no-any-return]

            result = _invoke()
            if isinstance(result, ExperimentPlan):
                return {"experiment_plan": result}
        except Exception:
            logger.exception("Failed to create ExperimentPlan")

        return {}

    def run(self, state: IStateContext) -> dict[str, Any]:
        """
        Run method. Delegates to generate_spec (default behavior).
        """
        return self.generate_spec(state)
