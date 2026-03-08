import logging
import time
from typing import Any

from src.agents.base import BaseAgent
from src.core.config import Settings, get_settings
from src.core.interfaces import LLMInterface
from src.domain_models import (
    AlternativeAnalysis,
    CustomerJourney,
    ExperimentPlan,
    MentalModelDiagram,
    SitemapAndStory,
    ValuePropositionCanvas,
)
from src.domain_models.persona import Persona
from src.domain_models.simulation import DialogueMessage, Role
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


class RemasteredAgent(BaseAgent):
    """
    Agent responsible for Phase 2 & 3 tasks of the Remastered workflow.
    Handles Persona, Alternative Analysis, VPC, Mental Model, Journey, Sitemap.
    """

    def __init__(self, llm: LLMInterface, app_settings: Settings | None = None) -> None:
        self.llm = llm
        self.settings = app_settings or get_settings()

    def generate_persona(self, state: GlobalState) -> dict[str, Any]:
        """Generate Persona based on the selected idea."""
        if not state.selected_idea:
            logger.warning("No idea selected for Persona generation.")
            return {}

        system_message = "You are an expert product researcher. Create a high-resolution Persona based on the provided business idea."
        prompt = f"Idea: {state.selected_idea.title}\nProblem: {state.selected_idea.problem}\nTarget: {state.selected_idea.customer_segments}\n\nGenerate Persona:"

        try:
            result = self.llm.generate_structured(prompt, Persona, system_message=system_message)
            if isinstance(result, Persona):
                return {"target_persona": result}
        except Exception:
            logger.exception("Failed to generate Persona")
        return {}

    def generate_alternative_analysis(self, state: GlobalState) -> dict[str, Any]:
        """Generate Alternative Analysis based on Persona and Idea."""
        if not state.selected_idea or not state.target_persona:
            logger.warning("Missing idea or persona for Alternative Analysis generation.")
            return {}

        system_message = "You are an expert market analyst. Identify current alternative methods (e.g., Excel, existing SaaS) and infer a '10x Value' that outweighs switching costs."
        prompt = f"Idea: {state.selected_idea.title}\nProblem: {state.selected_idea.problem}\nPersona: {state.target_persona.name} ({state.target_persona.occupation})\n\nGenerate Alternative Analysis:"

        try:
            result = self.llm.generate_structured(
                prompt, AlternativeAnalysis, system_message=system_message
            )
            if isinstance(result, AlternativeAnalysis):
                return {"alternative_analysis": result}
        except Exception:
            logger.exception("Failed to generate Alternative Analysis")
        return {}

    def generate_vpc(self, state: GlobalState) -> dict[str, Any]:
        """Generate Value Proposition Canvas based on previous contexts."""
        if not state.selected_idea or not state.target_persona:
            logger.warning("Missing context for VPC generation.")
            return {}

        system_message = "You are a product strategist. Create a Value Proposition Canvas validating how 'Pain Relievers' and 'Gain Creators' fit the customer's 'Jobs' and 'Pains/Gains'."
        prompt = f"Idea: {state.selected_idea.title}\nPersona: {state.target_persona.name} ({state.target_persona.occupation})\n\nGenerate Value Proposition Canvas:"

        try:
            result = self.llm.generate_structured(
                prompt, ValuePropositionCanvas, system_message=system_message
            )
            if isinstance(result, ValuePropositionCanvas):
                return {"value_proposition": result}
        except Exception:
            logger.exception("Failed to generate VPC")
        return {}

    def generate_mental_model_and_journey(self, state: GlobalState) -> dict[str, Any]:
        """Generate Mental Model and Customer Journey."""
        if not state.value_proposition or not state.alternative_analysis:
            logger.warning(
                "Missing VPC or Alternative Analysis for Mental Model/Journey generation."
            )
            return {}

        # 1. Mental Model Diagram
        system_message_mm = "You are a cognitive psychologist UX researcher. Visualize the 'Towers of Thought' behind the user's actions."
        prompt_mm = f"VPC Fit: {state.value_proposition.fit_evaluation}\nSwitching Cost: {state.alternative_analysis.switching_cost}\n\nGenerate Mental Model Diagram:"

        try:
            mm_result = self.llm.generate_structured(
                prompt_mm, MentalModelDiagram, system_message=system_message_mm
            )
        except Exception:
            logger.exception("Failed to generate Mental Model Diagram")
            return {}

        # 2. Customer Journey
        if isinstance(mm_result, MentalModelDiagram):
            mm_str = str(mm_result.model_dump())
            system_message_cj = "You are an expert UX researcher. Map chronological actions based on the mental model to a Customer Journey. You must ensure worst_pain_phase perfectly matches one of the phase_names."
            prompt_cj = f"Mental Model: {mm_str}\n\nGenerate Customer Journey:"

            try:
                cj_result = self.llm.generate_structured(
                    prompt_cj, CustomerJourney, system_message=system_message_cj
                )
                if isinstance(cj_result, CustomerJourney):
                    return {"mental_model": mm_result, "customer_journey": cj_result}
            except Exception:
                logger.exception("Failed to generate Customer Journey")
        return {}

    def generate_sitemap_and_wireframe(self, state: GlobalState) -> dict[str, Any]:
        """Generate Sitemap and Wireframe based on Customer Journey."""
        if not state.customer_journey:
            logger.warning("Missing Customer Journey for Sitemap generation.")
            return {}

        system_message = "You are an Information Architect. Define the entire URL structure and page transition overview of the app, and output a core UserStory targeting the worst pain phase."
        prompt = f"Worst Pain Phase: {state.customer_journey.worst_pain_phase}\nJourney Phases: {state.customer_journey.model_dump()!s}\n\nGenerate Sitemap and Story:"

        try:
            result = self.llm.generate_structured(
                prompt, SitemapAndStory, system_message=system_message
            )
            if isinstance(result, SitemapAndStory):
                return {"sitemap_and_story": result}
        except Exception:
            logger.exception("Failed to generate Sitemap and Story")
        return {}

    def run(self, state: GlobalState) -> dict[str, Any]:
        """BaseAgent requires run method. We split into specific methods, so this is unused."""
        return {}


class VirtualCustomerAgent(BaseAgent):
    """Virtual Market Test Agent."""

    def __init__(self, llm: LLMInterface, app_settings: Settings | None = None) -> None:
        self.llm = llm
        self.settings = app_settings or get_settings()

    def run(self, state: GlobalState) -> dict[str, Any]:
        """Review sitemap and story as a Virtual Customer."""
        if not state.sitemap_and_story or not state.target_persona:
            return {}

        system_message = "You are the Virtual Customer. Provide harsh feedback indicating whether you'd pay for the given user story or if switching costs are too high."
        prompt = f"Persona: {state.target_persona.model_dump()}\nStory: {state.sitemap_and_story.core_story.model_dump()}\n\nFeedback:"

        result_text = self.llm.generate(prompt, system_message=system_message)
        msg = DialogueMessage(role=Role.NEW_EMPLOYEE, content=result_text, timestamp=time.time())
        new_history = list(state.debate_history)
        new_history.append(msg)
        return {"debate_history": new_history}


class HackerAgent(BaseAgent):
    """Hacker Agent for 3H Review."""

    def __init__(self, llm: LLMInterface, app_settings: Settings | None = None) -> None:
        self.llm = llm
        self.settings = app_settings or get_settings()

    def run(self, state: GlobalState) -> dict[str, Any]:
        if not state.sitemap_and_story:
            return {}

        system_message = "You are the Hacker. Review the wireframe for technical debt, scalability, and security. Avoid unnecessary complexity."
        prompt = f"Sitemap: {state.sitemap_and_story.sitemap}\n\nTechnical Review:"

        result_text = self.llm.generate(prompt, system_message=system_message)
        msg = DialogueMessage(role=Role.FINANCE, content=result_text, timestamp=time.time())
        return {"debate_history": [msg]}


class HipsterAgent(BaseAgent):
    """Hipster Agent for 3H Review."""

    def __init__(self, llm: LLMInterface, app_settings: Settings | None = None) -> None:
        self.llm = llm
        self.settings = app_settings or get_settings()

    def run(self, state: GlobalState) -> dict[str, Any]:
        if not state.mental_model or not state.sitemap_and_story:
            return {}

        system_message = "You are the Hipster. Review the UX based on 'Don't make me think'. Point out friction against the mental model."
        prompt = f"Mental Model: {state.mental_model.model_dump()}\nStory: {state.sitemap_and_story.core_story.model_dump()}\n\nUX Review:"

        result_text = self.llm.generate(prompt, system_message=system_message)
        msg = DialogueMessage(role=Role.SALES, content=result_text, timestamp=time.time())
        return {"debate_history": [msg]}


class HustlerAgent(BaseAgent):
    """Hustler Agent for 3H Review."""

    def __init__(self, llm: LLMInterface, app_settings: Settings | None = None) -> None:
        self.llm = llm
        self.settings = app_settings or get_settings()

    def run(self, state: GlobalState) -> dict[str, Any]:
        if not state.alternative_analysis or not state.value_proposition:
            return {}

        system_message = "You are the Hustler. Review the business model unit economics (LTV > 3x CAC). Interrogate who will pay and why."
        prompt = f"Alternatives: {state.alternative_analysis.model_dump()}\nVPC: {state.value_proposition.model_dump()}\n\nBusiness Review:"

        result_text = self.llm.generate(prompt, system_message=system_message)
        msg = DialogueMessage(role=Role.CPO, content=result_text, timestamp=time.time())
        return {"debate_history": [msg]}


class OutputGenerationAgent(BaseAgent):
    """Agent for Phase 5 & 6 (Agent Prompt Spec & Experiment Plan)."""

    def __init__(self, llm: LLMInterface, app_settings: Settings | None = None) -> None:
        self.llm = llm
        self.settings = app_settings or get_settings()

    def generate_experiment_plan(self, state: GlobalState) -> dict[str, Any]:
        """Generate Experiment Plan."""
        if not state.selected_idea:
            logger.warning("Missing idea for Experiment Plan.")
            return {}

        system_message = "You are a growth hacker. Generate an Experiment Plan defining 'What and How to measure' using the MVP."
        prompt = f"Idea: {state.selected_idea.title}\n\nGenerate Experiment Plan:"

        try:
            result = self.llm.generate_structured(
                prompt, ExperimentPlan, system_message=system_message
            )
            if isinstance(result, ExperimentPlan):
                return {"experiment_plan": result}
        except Exception:
            logger.exception("Failed to generate Experiment Plan")
        return {}

    def run(self, state: GlobalState) -> dict[str, Any]:
        return {}
