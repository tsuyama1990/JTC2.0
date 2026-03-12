import logging
from typing import Any

from src.agents.base import BaseAgent
from src.core.config import get_settings
from src.core.interfaces import ILLMClient
from src.domain_models.customer_journey import CustomerJourney
from src.domain_models.mental_model_diagram import MentalModelDiagram
from src.domain_models.sitemap_and_story import SitemapAndStory
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


class MentalModelJourneyAgent(BaseAgent):
    """
    Agent responsible for Phase 3, Step 6: Mental Model & Journey Mapping.
    """

    def __init__(self, llm: ILLMClient) -> None:
        self.llm = llm
        self.settings = get_settings()

    def run(self, state: GlobalState) -> dict[str, Any]:
        if not state.target_persona or not state.value_proposition_canvas:
            logger.warning("Missing required context for Mental Model & Journey Mapping.")
            return {}

        prompt_messages = [
            {
                "role": "system",
                "content": "You are an expert UX researcher. Generate a Mental Model Diagram and a Customer Journey based on the provided context.",
            },
            {
                "role": "user",
                "content": f"Persona: {state.target_persona.model_dump_json()}\n"
                f"VPC: {state.value_proposition_canvas.model_dump_json()}\n"
                "Generate Mental Model Diagram:",
            },
        ]

        try:
            structured_llm = self.llm.with_structured_output(MentalModelDiagram)
            mm_result = structured_llm.invoke(prompt_messages)
        except Exception:
            logger.exception("Failed to generate Mental Model Diagram")
            return {}

        if not isinstance(mm_result, MentalModelDiagram):
            return {}

        journey_prompt_messages = [
            {
                "role": "system",
                "content": "You are an expert UX researcher. Generate a Customer Journey based on the Mental Model.",
            },
            {
                "role": "user",
                "content": f"Mental Model: {mm_result.model_dump_json()}\n"
                f"Persona: {state.target_persona.model_dump_json()}\n"
                "Generate Customer Journey:",
            },
        ]

        journey_llm = self.llm.with_structured_output(CustomerJourney)
        max_retries = 3
        valid_beliefs = {tower.belief for tower in mm_result.towers}

        journey_result = self._retry_journey_generation(
            journey_llm, journey_prompt_messages, valid_beliefs, max_retries
        )

        if journey_result:
            return {"mental_model_diagram": mm_result, "customer_journey": journey_result}

        logger.error("Failed to map Mental Model to Customer Journey after max retries.")
        # Trigger fallback strategy
        messages = list(state.messages) if state.messages else []
        messages.append(
            "Please simplify the Persona complexity. Failed to logically map mental models to a journey."
        )

        return {"mental_model_diagram": mm_result, "messages": messages}

    def _retry_journey_generation(
        self,
        journey_llm: Any,
        journey_prompt_messages: list[dict[str, Any]],
        valid_beliefs: set[str],
        max_retries: int,
    ) -> CustomerJourney | None:
        from pydantic import ValidationError
        from pydantic_core import InitErrorDetails, PydanticCustomError

        def validate_journey(journey: CustomerJourney) -> None:
            for phase in journey.phases:
                if phase.mental_tower_ref not in valid_beliefs:
                    msg = f"Invalid mental_tower_ref: {phase.mental_tower_ref}. Must be one of {valid_beliefs}"
                    raise ValidationError.from_exception_data(
                        title=CustomerJourney.__name__,
                        line_errors=[
                            InitErrorDetails(
                                type=PydanticCustomError("invalid_ref", msg),
                                loc=("phases", "mental_tower_ref"),
                                input=phase.mental_tower_ref,
                            )
                        ],
                    )

        for attempt in range(max_retries):
            try:
                journey_result = journey_llm.invoke(journey_prompt_messages)

                if not isinstance(journey_result, CustomerJourney):
                    continue

                validate_journey(journey_result)

            except ValidationError as e:
                logger.warning(f"Journey validation failed on attempt {attempt + 1}: {e}")
                error_msg = f"Validation Error: {e}. Ensure mental_tower_ref exactly matches a belief in MentalModelDiagram towers."
                journey_prompt_messages.append({"role": "user", "content": error_msg})
            except Exception:
                logger.exception("Failed to generate Customer Journey")
                break
            else:
                return journey_result

        return None


class SitemapWireframeAgent(BaseAgent):
    """
    Agent responsible for Phase 3, Step 7: Sitemap & Lo-Fi Wireframing.
    """

    def __init__(self, llm: ILLMClient) -> None:
        self.llm = llm
        self.settings = get_settings()

    def run(self, state: GlobalState) -> dict[str, Any]:
        if not state.customer_journey:
            logger.warning("Missing Customer Journey for Sitemap generation.")
            return {}

        prompt_messages = [
            {
                "role": "system",
                "content": "You are an expert Information Architect. Generate a Sitemap and Core User Story.",
            },
            {
                "role": "user",
                "content": f"Customer Journey: {state.customer_journey.model_dump_json()}\n"
                "Generate SitemapAndStory:",
            },
        ]

        try:
            structured_llm = self.llm.with_structured_output(SitemapAndStory)
            result = structured_llm.invoke(prompt_messages)
            if isinstance(result, SitemapAndStory):
                return {"sitemap_and_story": result}
        except Exception:
            logger.exception("Failed to generate Sitemap and Story")

        return {}
