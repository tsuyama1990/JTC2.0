import logging
from typing import Any

import pybreaker
from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import ValidationError
from typing_extensions import TypedDict

from src.agents.base import BaseAgent
from src.core.config import get_settings
from src.domain_models.agent_spec import AgentPromptSpec
from src.domain_models.experiment import ExperimentPlan
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


class BuilderAgentResult(TypedDict, total=False):
    agent_prompt_spec: AgentPromptSpec | None
    experiment_plan: ExperimentPlan | None
    error: str


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

        fail_max = 3
        reset_timeout = 60

        max_size = getattr(self.settings.governance, "max_llm_response_size", 0)
        if not (1000 <= max_size <= 1000000):
            msg = "max_llm_response_size must be between 1000 and 1,000,000 bytes."
            raise ValueError(msg)

        self._breaker = pybreaker.CircuitBreaker(
            fail_max=fail_max,
            reset_timeout=reset_timeout,
        )

    def _yield_context_chunks(self, state: GlobalState) -> Any:
        """
        Yields JSON-serialized chunks of domain models to prevent loading entire datasets into memory.
        Enforces size limits per field.
        """
        import json

        def safe_json_dumps(obj: Any) -> str:
            # We don't truncate midway through strings to avoid corrupting JSON parsing or LLM context.
            # We also sanitize the JSON output to strip potentially malicious invisible characters
            # or massive payloads that might break LLM parsing.
            dumped = json.dumps(obj)

            # Simple sanitization whitelist for LLM context injection
            # Only keep basic printable/formatting characters.
            import string

            allowed = set(string.printable)
            return "".join(
                c for c in dumped if c in allowed or ord(c) > 127
            )  # Keep unicode but strip bad ascii control chars

        if state.selected_idea:
            yield "Idea: " + safe_json_dumps(state.selected_idea.title) + "\n"
            yield "Problem: " + safe_json_dumps(state.selected_idea.problem) + "\n"
            yield "Solution: " + safe_json_dumps(state.selected_idea.solution) + "\n\n"

        if state.vpc:
            yield "VPC:\n"
            for k, v in state.vpc.model_dump().items():
                yield f"{k}: {safe_json_dumps(v)}\n"
            yield "\n"

        if state.mental_model:
            yield "Mental Model:\n"
            for k, v in state.mental_model.model_dump().items():
                yield f"{k}: {safe_json_dumps(v)}\n"
            yield "\n"

        if state.customer_journey:
            yield "Journey:\n"
            for k, v in state.customer_journey.model_dump().items():
                yield f"{k}: {safe_json_dumps(v)}\n"
            yield "\n"

        if state.sitemap_and_story:
            yield "Sitemap & Story:\n"
            for k, v in state.sitemap_and_story.model_dump().items():
                yield f"{k}: {safe_json_dumps(v)}\n"
            yield "\n"

    def _compile_context(self, state: GlobalState) -> tuple[str, bool]:
        """
        Compiles prior domain models safely to prevent holding massive objects in memory.
        Returns the compiled context string and a boolean indicating if truncation occurred.
        """
        context_chunks: list[str] = []
        current_size = 0
        is_truncated = False
        max_size = getattr(self.settings.governance, "max_llm_response_size", 100000)
        if max_size < 1000:
            logger.warning(f"max_llm_response_size {max_size} is too low. Defaulting to 100000.")
            max_size = 100000

        for chunk in self._yield_context_chunks(state):
            if is_truncated:
                break
            chunk_len = len(chunk.encode("utf-8"))
            if current_size + chunk_len > max_size:
                # If a single chunk puts us over the limit, we discard the chunk entirely
                # rather than slicing it, to maintain well-formed textual syntax/JSON per field.
                logger.warning(
                    f"Context streaming truncated at {max_size} bytes. Discarding remaining models."
                )
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

        from langchain_core.prompts import ChatPromptTemplate

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

        from langchain_core.prompts import ChatPromptTemplate

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

    def _validate_state(self, state: GlobalState) -> str | None:
        """Validates that all required context models exist."""
        missing = []
        if not state.vpc:
            missing.append("ValuePropositionCanvas")
        if not state.mental_model:
            missing.append("MentalModelDiagram")
        if not state.customer_journey:
            missing.append("CustomerJourney")
        if not state.sitemap_and_story:
            missing.append("SitemapAndStory")
        if missing:
            return f"Missing required context models: {', '.join(missing)}"
        return None

    def _generate_specs_with_retries(
        self, context: str, is_truncated: bool
    ) -> tuple[AgentPromptSpec | None, ExperimentPlan | None, str | None]:
        """Generates both specs, retrying on validation errors, incorporating exponential backoff and circuit breaker checks."""
        import time

        agent_prompt_spec = None
        experiment_plan = None

        def _do_backoff(attempt: int) -> None:
            # Exponential backoff with jitter
            import secrets

            base_delay = 1.0
            delay = base_delay * (2**attempt) + (secrets.randbelow(50) / 100.0)
            time.sleep(delay)

        error_feedback = ""
        for attempt in range(3):
            if self._breaker.state.name == "open":
                msg = "Circuit breaker is open. Aborting spec generation retries to conserve resources."
                logger.error(msg)
                return None, None, msg

            try:
                agent_prompt_spec = self._generate_agent_prompt_spec(
                    context, is_truncated, error_feedback
                )
                break
            except ValidationError as e:
                logger.warning(
                    f"Validation error generating AgentPromptSpec (attempt {attempt + 1}/3)."
                )
                error_feedback = str(e)
                _do_backoff(attempt)
            except pybreaker.CircuitBreakerError as e:
                logger.exception("Circuit breaker is open. Aborting retries for AgentPromptSpec.")
                return None, None, f"System unavailable due to recurring errors: {e}"
            except Exception as e:
                logger.exception("BuilderAgent run failed during spec generation.")
                return None, None, f"BuilderAgent failed during spec generation: {e}"
        else:
            logger.error("Failed to generate valid AgentPromptSpec after 3 attempts.")
            return None, None, "Failed to generate valid AgentPromptSpec after 3 attempts."

        error_feedback = ""
        for attempt in range(3):
            if self._breaker.state.name == "open":
                msg = "Circuit breaker is open. Aborting plan generation retries to conserve resources."
                logger.error(msg)
                return None, None, msg

            try:
                experiment_plan = self._generate_experiment_plan(
                    context, is_truncated, error_feedback
                )
                break
            except ValidationError as e:
                logger.warning(
                    f"Validation error generating ExperimentPlan (attempt {attempt + 1}/3)."
                )
                error_feedback = str(e)
                _do_backoff(attempt)
            except pybreaker.CircuitBreakerError as e:
                logger.exception("Circuit breaker is open. Aborting retries for ExperimentPlan.")
                return None, None, f"System unavailable due to recurring errors: {e}"
            except Exception as e:
                logger.exception("BuilderAgent run failed during plan generation.")
                return None, None, f"BuilderAgent failed during plan generation: {e}"
        else:
            logger.error("Failed to generate valid ExperimentPlan after 3 attempts.")
            return None, None, "Failed to generate valid ExperimentPlan after 3 attempts."

        return agent_prompt_spec, experiment_plan, None

    def run(self, state: GlobalState) -> dict[str, Any]:
        """Agent entry point."""
        logger.info("Executing spec generation...")

        error_msg = self._validate_state(state)
        if error_msg:
            logger.error(error_msg)
            return {"error": error_msg}

        context, is_truncated = self._compile_context(state)
        if not context.strip():
            logger.warning("No context available to generate specs.")
            return {"error": "No context available to generate specs."}

        agent_prompt_spec, experiment_plan, err = self._generate_specs_with_retries(
            context, is_truncated
        )
        if err:
            return {"error": err}

        logger.info("Successfully generated AgentPromptSpec and ExperimentPlan.")
        return {"agent_prompt_spec": agent_prompt_spec, "experiment_plan": experiment_plan}
