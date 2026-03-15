import logging
from typing import Any

import pybreaker
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

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

    def __init__(self, llm: ChatOpenAI) -> None:
        self.llm = llm
        self.settings = get_settings()
        self._breaker = pybreaker.CircuitBreaker(
            fail_max=self.settings.circuit_breaker_fail_max,
            reset_timeout=self.settings.circuit_breaker_reset_timeout,
        )

    def _compile_context(self, state: GlobalState) -> str:
        """Compiles prior domain models into a single string for the LLM."""
        context_parts = []
        if state.selected_idea:
            context_parts.append(f"Idea: {state.selected_idea.title}")
            context_parts.append(f"Problem: {state.selected_idea.problem}")
            context_parts.append(f"Solution: {state.selected_idea.solution}")
        if state.vpc:
            context_parts.append(f"VPC: {state.vpc.model_dump_json(indent=2)}")
        if state.mental_model:
            context_parts.append(f"Mental Model: {state.mental_model.model_dump_json(indent=2)}")
        if state.customer_journey:
            context_parts.append(f"Journey: {state.customer_journey.model_dump_json(indent=2)}")
        if state.sitemap_and_story:
            context_parts.append(
                f"Sitemap & Story: {state.sitemap_and_story.model_dump_json(indent=2)}"
            )

        final_context = "\n\n".join(context_parts)
        max_size = getattr(self.settings.governance, "max_llm_response_size", 10000) * 10
        if len(final_context) > max_size:
            logger.warning("Compiled context exceeded max size. Truncating.")
            return final_context[:max_size] + "\n...[TRUNCATED]"

        return final_context

    @retry(
        retry=retry_if_exception_type(ValidationError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _generate_agent_prompt_spec(
        self, context: str, error_feedback: str = ""
    ) -> AgentPromptSpec:
        """Generates the AgentPromptSpec with self-correction retry loop."""
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
        except ValidationError as e:
            logger.warning(f"Validation error generating AgentPromptSpec. Retrying... Details: {e}")
            raise

    @retry(
        retry=retry_if_exception_type(ValidationError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _generate_experiment_plan(self, context: str, error_feedback: str = "") -> ExperimentPlan:
        """Generates the ExperimentPlan with self-correction retry loop."""
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
        except ValidationError as e:
            logger.warning(f"Validation error generating ExperimentPlan. Retrying... Details: {e}")
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

        try:
            agent_prompt_spec = self._generate_agent_prompt_spec(context)
            experiment_plan = self._generate_experiment_plan(context)
        except Exception:
            logger.exception("BuilderAgent run failed during spec generation.")
            return {}
        else:
            logger.info("Successfully generated AgentPromptSpec and ExperimentPlan.")
            return {"agent_prompt_spec": agent_prompt_spec, "experiment_plan": experiment_plan}
