import logging
from typing import Any

import pybreaker
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from pydantic import ValidationError

from src.agents.base import BaseAgent
from src.core.config import get_settings
from src.domain_models.agent_spec import AgentPromptSpec
from src.domain_models.experiment import ExperimentPlan
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


class BuilderAgent(BaseAgent):
    """
    Agent responsible for generating the final specifications (Cycle 5).
    Replaces the old v0.dev direct integration with rigorous prompt spec generation.
    It reads all prior context (VPC, Mental Model, Journey, Sitemap) and generates
    the AgentPromptSpec and ExperimentPlan.
    """

    def __init__(self, llm: BaseChatModel) -> None:
        self.llm = llm
        self.settings = get_settings()
        self._breaker = pybreaker.CircuitBreaker(
            fail_max=self.settings.circuit_breaker_fail_max,
            reset_timeout=self.settings.circuit_breaker_reset_timeout,
        )

    def _compile_context(self, state: GlobalState) -> str:  # noqa: C901
        """Compiles prior domain models into a single string for the LLM, truncating parts safely to avoid OOM."""
        import json

        def truncate_dict_strings(d: Any, max_str_len: int = 500) -> Any:
            """Recursively truncate string values in a dictionary to prevent JSON malformation."""
            if isinstance(d, dict):
                return {k: truncate_dict_strings(v, max_str_len) for k, v in d.items()}
            if isinstance(d, list):
                return [truncate_dict_strings(v, max_str_len) for v in d]
            if isinstance(d, str) and len(d) > max_str_len:
                return d[:max_str_len] + "...[TRUNC]"
            return d

        def _safe_dump(model: Any) -> str:
            raw_dict = model.model_dump(mode="json")
            truncated_dict = truncate_dict_strings(raw_dict)
            return json.dumps(truncated_dict, indent=2)

        context_parts = []
        if state.selected_idea:
            context_parts.append(f"Idea: {state.selected_idea.title}")
            context_parts.append(f"Problem: {state.selected_idea.problem}")
            context_parts.append(f"Solution: {state.selected_idea.solution}")
        if state.vpc:
            context_parts.append(f"VPC: {_safe_dump(state.vpc)}")
        if state.mental_model:
            context_parts.append(f"Mental Model: {_safe_dump(state.mental_model)}")
        if state.customer_journey:
            context_parts.append(f"Journey: {_safe_dump(state.customer_journey)}")
        if state.sitemap_and_story:
            context_parts.append(f"Sitemap & Story: {_safe_dump(state.sitemap_and_story)}")

        final_context = "\n\n".join(context_parts)
        max_size = getattr(self.settings.governance, "max_llm_response_size", 10000) * 10
        if len(final_context) > max_size:
            logger.warning("Compiled context still exceeded max size after dictionary truncation.")
            return final_context[:max_size]

        return final_context

    def _generate_agent_prompt_spec(
        self, context: str, error_feedback: str = ""
    ) -> AgentPromptSpec:
        """Generates the AgentPromptSpec."""
        sys_msg = (
            "You are an expert Frontend Architect and Product Manager. "
            "Using the provided context, generate the ultimate Markdown prompt spec for AI coders (like Cursor/Windsurf). "
            "You must apply 'subtraction thinking' to remove unnecessary features."
        )
        if error_feedback:
            sys_msg += f"\n\nPREVIOUS ERROR TO FIX:\n{error_feedback}"

        prompt = ChatPromptTemplate.from_messages(
            [("system", sys_msg), ("user", "Context:\n{context}")]
        )

        chain = prompt | self.llm.with_structured_output(AgentPromptSpec)
        try:
            result = self._breaker.call(chain.invoke, {"context": context})
            if isinstance(result, AgentPromptSpec):
                return result
            msg = f"Expected AgentPromptSpec, got {type(result)}"
            raise ValueError(msg)
        except pybreaker.CircuitBreakerError:
            logger.exception("Circuit breaker tripped generating AgentPromptSpec")
            raise

    def _generate_experiment_plan(self, context: str, error_feedback: str = "") -> ExperimentPlan:
        """Generates the ExperimentPlan."""
        sys_msg = (
            "You are a growth hacker. Generate an Experiment Plan to test the riskiest assumption of this MVP. "
            "Define the acquisition channel, AARRR metrics targets, and the pivot condition."
        )
        if error_feedback:
            sys_msg += f"\n\nPREVIOUS ERROR TO FIX:\n{error_feedback}"

        prompt = ChatPromptTemplate.from_messages(
            [("system", sys_msg), ("user", "Context:\n{context}")]
        )

        chain = prompt | self.llm.with_structured_output(ExperimentPlan)
        try:
            result = self._breaker.call(chain.invoke, {"context": context})
            if isinstance(result, ExperimentPlan):
                return result
            msg = f"Expected ExperimentPlan, got {type(result)}"
            raise ValueError(msg)
        except pybreaker.CircuitBreakerError:
            logger.exception("Circuit breaker tripped generating ExperimentPlan")
            raise

    def run(self, state: GlobalState) -> dict[str, Any]:
        """
        Agent entry point.
        """
        logger.info("Executing spec generation...")
        context = self._compile_context(state)

        if not context.strip():
            logger.warning("No context available to generate specs.")
            return {}

        agent_prompt_spec = None
        experiment_plan = None

        # Self-correction loop for AgentPromptSpec
        error_feedback = ""
        for attempt in range(3):
            try:
                agent_prompt_spec = self._generate_agent_prompt_spec(context, error_feedback)
                break
            except ValidationError as e:
                logger.warning(f"Validation error generating AgentPromptSpec (attempt {attempt+1}/3).")
                error_feedback = str(e)
            except Exception:
                logger.exception("BuilderAgent run failed during spec generation.")
                return {}
        else:
            logger.error("Failed to generate valid AgentPromptSpec after 3 attempts.")
            return {}

        # Self-correction loop for ExperimentPlan
        error_feedback = ""
        for attempt in range(3):
            try:
                experiment_plan = self._generate_experiment_plan(context, error_feedback)
                break
            except ValidationError as e:
                logger.warning(f"Validation error generating ExperimentPlan (attempt {attempt+1}/3).")
                error_feedback = str(e)
            except Exception:
                logger.exception("BuilderAgent run failed during plan generation.")
                return {}
        else:
            logger.error("Failed to generate valid ExperimentPlan after 3 attempts.")
            return {}

        logger.info("Successfully generated AgentPromptSpec and ExperimentPlan.")
        return {"agent_prompt_spec": agent_prompt_spec, "experiment_plan": experiment_plan}
