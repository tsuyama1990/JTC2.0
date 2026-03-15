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

        fail_max = self.settings.circuit_breaker_fail_max
        reset_timeout = self.settings.circuit_breaker_reset_timeout
        if not (1 <= fail_max <= 10):
            msg = "circuit_breaker_fail_max must be between 1 and 10."
            raise ValueError(msg)
        if not (10 <= reset_timeout <= 300):
            msg = "circuit_breaker_reset_timeout must be between 10 and 300."
            raise ValueError(msg)

        self._breaker = pybreaker.CircuitBreaker(
            fail_max=fail_max,
            reset_timeout=reset_timeout,
        )

    def _compile_context(self, state: GlobalState) -> tuple[str, bool]:
        """
        Compiles prior domain models using a generator to prevent holding massive objects in memory.
        Returns the compiled context string and a boolean indicating if truncation occurred.
        """
        from collections.abc import Iterator

        def _stream_context() -> Iterator[str]:
            if state.selected_idea:
                yield f"Idea: {state.selected_idea.title}\n"
                yield f"Problem: {state.selected_idea.problem}\n"
                yield f"Solution: {state.selected_idea.solution}\n\n"

            def _yield_model(name: str, model: Any) -> Iterator[str]:
                yield f"{name}: "
                # Replace JSONEncoder.iterencode with secure model_dump_json for Pydantic
                json_str = model.model_dump_json(indent=2)
                yield json_str
                yield "\n\n"

            if state.vpc:
                yield from _yield_model("VPC", state.vpc)
            if state.mental_model:
                yield from _yield_model("Mental Model", state.mental_model)
            if state.customer_journey:
                yield from _yield_model("Journey", state.customer_journey)
            if state.sitemap_and_story:
                yield from _yield_model("Sitemap & Story", state.sitemap_and_story)

        max_size = getattr(self.settings.governance, "max_llm_response_size", 10000) * 10
        current_size = 0
        context_chunks: list[str] = []
        is_truncated = False

        for chunk in _stream_context():
            chunk_len = len(chunk)
            if current_size + chunk_len > max_size:
                context_chunks.append(chunk[: max_size - current_size])
                logger.warning(f"Context streaming truncated at {max_size} characters.")
                is_truncated = True
                break
            context_chunks.append(chunk)
            current_size += chunk_len

        return "".join(context_chunks), is_truncated

    def _generate_agent_prompt_spec(
        self, context: str, is_truncated: bool, error_feedback: str = ""
    ) -> AgentPromptSpec:
        """Generates the AgentPromptSpec."""
        sys_msg = (
            "You are an expert Frontend Architect and Product Manager. "
            "Using the provided context, generate the ultimate Markdown prompt spec for AI coders (like Cursor/Windsurf). "
            "You must apply 'subtraction thinking' to remove unnecessary features."
        )
        if is_truncated:
            sys_msg += "\n\nWARNING: The input context was truncated. Some fields may be incomplete. Provide your best effort given the data available."
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
            raise ValueError(msg)  # noqa: TRY301
        except pybreaker.CircuitBreakerError:
            logger.exception("Circuit breaker tripped generating AgentPromptSpec")
            raise
        except Exception as e:
            logger.exception("Unexpected error generating AgentPromptSpec")
            msg = f"Failed to generate AgentPromptSpec: {e}"
            raise ValueError(msg) from e

    def _generate_experiment_plan(
        self, context: str, is_truncated: bool, error_feedback: str = ""
    ) -> ExperimentPlan:
        """Generates the ExperimentPlan."""
        sys_msg = (
            "You are a growth hacker. Generate an Experiment Plan to test the riskiest assumption of this MVP. "
            "Define the acquisition channel, AARRR metrics targets, and the pivot condition."
        )
        if is_truncated:
            sys_msg += "\n\nWARNING: The input context was truncated. Some fields may be incomplete. Provide your best effort given the data available."
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
            raise ValueError(msg)  # noqa: TRY301
        except pybreaker.CircuitBreakerError:
            logger.exception("Circuit breaker tripped generating ExperimentPlan")
            raise
        except Exception as e:
            logger.exception("Unexpected error generating ExperimentPlan")
            msg = f"Failed to generate ExperimentPlan: {e}"
            raise ValueError(msg) from e

    def run(self, state: GlobalState) -> dict[str, Any]:
        """
        Agent entry point.
        """
        logger.info("Executing spec generation...")
        context, is_truncated = self._compile_context(state)

        if not context.strip():
            logger.warning("No context available to generate specs.")
            return {"error": "No context available to generate specs."}

        agent_prompt_spec = None
        experiment_plan = None

        # Self-correction loop for AgentPromptSpec
        error_feedback = ""
        for attempt in range(3):
            try:
                agent_prompt_spec = self._generate_agent_prompt_spec(context, is_truncated, error_feedback)
                break
            except ValidationError as e:
                logger.warning(
                    f"Validation error generating AgentPromptSpec (attempt {attempt + 1}/3)."
                )
                error_feedback = str(e)
            except Exception as e:
                logger.exception("BuilderAgent run failed during spec generation.")
                return {"error": f"BuilderAgent failed during spec generation: {e}"}
        else:
            logger.error("Failed to generate valid AgentPromptSpec after 3 attempts.")
            return {"error": "Failed to generate valid AgentPromptSpec after 3 attempts."}

        # Self-correction loop for ExperimentPlan
        error_feedback = ""
        for attempt in range(3):
            try:
                experiment_plan = self._generate_experiment_plan(context, is_truncated, error_feedback)
                break
            except ValidationError as e:
                logger.warning(
                    f"Validation error generating ExperimentPlan (attempt {attempt + 1}/3)."
                )
                error_feedback = str(e)
            except Exception as e:
                logger.exception("BuilderAgent run failed during plan generation.")
                return {"error": f"BuilderAgent failed during plan generation: {e}"}
        else:
            logger.error("Failed to generate valid ExperimentPlan after 3 attempts.")
            return {"error": "Failed to generate valid ExperimentPlan after 3 attempts."}

        logger.info("Successfully generated AgentPromptSpec and ExperimentPlan.")
        return {"agent_prompt_spec": agent_prompt_spec, "experiment_plan": experiment_plan}
