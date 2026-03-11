import logging
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.agents.base import BaseAgent
from src.core.config import get_settings
from src.domain_models.customer_journey import CustomerJourney
from src.domain_models.mental_model_diagram import MentalModelDiagram
from src.domain_models.sitemap_and_story import SitemapAndStory
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


class MentalModelJourneyAgent(BaseAgent):
    """
    Agent responsible for Phase 3, Step 6: Mental Model & Journey Mapping.
    """

    def __init__(self, llm: ChatOpenAI) -> None:
        self.llm = llm
        self.settings = get_settings()

    def run(self, state: GlobalState) -> dict[str, Any]:
        if not state.target_persona or not state.value_proposition_canvas:
            logger.warning("Missing required context for Mental Model & Journey Mapping.")
            return {}

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert UX researcher. Generate a Mental Model Diagram and a Customer Journey based on the provided context.",
                ),
                (
                    "user",
                    f"Persona: {state.target_persona.model_dump_json()}\n"
                    f"VPC: {state.value_proposition_canvas.model_dump_json()}\n"
                    "Generate Mental Model Diagram:",
                ),
            ]
        )
        mm_chain = prompt | self.llm.with_structured_output(MentalModelDiagram)

        try:
            mm_result = mm_chain.invoke({})
        except Exception:
            logger.exception("Failed to generate Mental Model Diagram")
            return {}

        if not isinstance(mm_result, MentalModelDiagram):
            return {}

        journey_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert UX researcher. Generate a Customer Journey based on the Mental Model.",
                ),
                (
                    "user",
                    f"Mental Model: {mm_result.model_dump_json()}\n"
                    f"Persona: {state.target_persona.model_dump_json()}\n"
                    "Generate Customer Journey:",
                ),
            ]
        )
        journey_chain = journey_prompt | self.llm.with_structured_output(CustomerJourney)

        try:
            journey_result = journey_chain.invoke({})
        except Exception:
            logger.exception("Failed to generate Customer Journey")
            return {"mental_model_diagram": mm_result}

        if isinstance(journey_result, CustomerJourney):
            return {"mental_model_diagram": mm_result, "customer_journey": journey_result}

        return {"mental_model_diagram": mm_result}


class SitemapWireframeAgent(BaseAgent):
    """
    Agent responsible for Phase 3, Step 7: Sitemap & Lo-Fi Wireframing.
    """

    def __init__(self, llm: ChatOpenAI) -> None:
        self.llm = llm
        self.settings = get_settings()

    def run(self, state: GlobalState) -> dict[str, Any]:
        if not state.customer_journey:
            logger.warning("Missing Customer Journey for Sitemap generation.")
            return {}

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert Information Architect. Generate a Sitemap and Core User Story.",
                ),
                (
                    "user",
                    f"Customer Journey: {state.customer_journey.model_dump_json()}\n"
                    "Generate SitemapAndStory:",
                ),
            ]
        )
        chain = prompt | self.llm.with_structured_output(SitemapAndStory)

        try:
            result = chain.invoke({})
            if isinstance(result, SitemapAndStory):
                return {"sitemap_and_story": result}
        except Exception:
            logger.exception("Failed to generate Sitemap and Story")

        return {}
