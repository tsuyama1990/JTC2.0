import logging
import time
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.agents.base import BaseAgent
from src.core.config import Settings, get_settings
from src.domain_models import (
    AgentPromptSpec,
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

    def __init__(self, llm: ChatOpenAI, app_settings: Settings | None = None) -> None:
        self.llm = llm
        self.settings = app_settings or get_settings()

    def generate_persona(self, state: GlobalState) -> dict[str, Any]:
        """Generate Persona based on the selected idea."""
        if not state.selected_idea:
            logger.warning("No idea selected for Persona generation.")
            return {}

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert product researcher. Create a high-resolution Persona based on the provided business idea.",
                ),
                (
                    "user",
                    f"Idea: {state.selected_idea.title}\nProblem: {state.selected_idea.problem}\nTarget: {state.selected_idea.customer_segments}\n\nGenerate Persona:",
                ),
            ]
        )
        chain = prompt | self.llm.with_structured_output(Persona)
        try:
            result = chain.invoke({})
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

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert market analyst. Identify current alternative methods (e.g., Excel, existing SaaS) and infer a '10x Value' that outweighs switching costs.",
                ),
                (
                    "user",
                    f"Idea: {state.selected_idea.title}\nProblem: {state.selected_idea.problem}\nPersona: {state.target_persona.name} ({state.target_persona.occupation})\n\nGenerate Alternative Analysis:",
                ),
            ]
        )
        chain = prompt | self.llm.with_structured_output(AlternativeAnalysis)
        try:
            result = chain.invoke({})
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

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a product strategist. Create a Value Proposition Canvas validating how 'Pain Relievers' and 'Gain Creators' fit the customer's 'Jobs' and 'Pains/Gains'.",
                ),
                (
                    "user",
                    f"Idea: {state.selected_idea.title}\nPersona: {state.target_persona.name} ({state.target_persona.occupation})\n\nGenerate Value Proposition Canvas:",
                ),
            ]
        )
        chain = prompt | self.llm.with_structured_output(ValuePropositionCanvas)
        try:
            result = chain.invoke({})
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
        mm_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a cognitive psychologist UX researcher. Visualize the 'Towers of Thought' behind the user's actions.",
                ),
                (
                    "user",
                    f"VPC Fit: {state.value_proposition.fit_evaluation}\nSwitching Cost: {state.alternative_analysis.switching_cost}\n\nGenerate Mental Model Diagram:",
                ),
            ]
        )
        mm_chain = mm_prompt | self.llm.with_structured_output(MentalModelDiagram)
        try:
            mm_result = mm_chain.invoke({})
        except Exception:
            logger.exception("Failed to generate Mental Model Diagram")
            return {}

        # 2. Customer Journey
        if isinstance(mm_result, MentalModelDiagram):
            mm_str = str(mm_result.model_dump())
            cj_prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are an expert UX researcher. Map chronological actions based on the mental model to a Customer Journey. You must ensure worst_pain_phase perfectly matches one of the phase_names.",
                    ),
                    ("user", f"Mental Model: {mm_str}\n\nGenerate Customer Journey:"),
                ]
            )
            cj_chain = cj_prompt | self.llm.with_structured_output(CustomerJourney)
            try:
                cj_result = cj_chain.invoke({})
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

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an Information Architect. Define the entire URL structure and page transition overview of the app, and output a core UserStory targeting the worst pain phase.",
                ),
                (
                    "user",
                    f"Worst Pain Phase: {state.customer_journey.worst_pain_phase}\nJourney Phases: {state.customer_journey.model_dump()!s}\n\nGenerate Sitemap and Story:",
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

    def run(self, state: GlobalState) -> dict[str, Any]:
        """BaseAgent requires run method. We split into specific methods, so this is unused."""
        return {}


class VirtualCustomerAgent(BaseAgent):
    """Virtual Market Test Agent."""

    def __init__(self, llm: ChatOpenAI, app_settings: Settings | None = None) -> None:
        self.llm = llm
        self.settings = app_settings or get_settings()

    def run(self, state: GlobalState) -> dict[str, Any]:
        """Review sitemap and story as a Virtual Customer."""
        if not state.sitemap_and_story or not state.target_persona:
            return {}
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are the Virtual Customer. Provide harsh feedback indicating whether you'd pay for the given user story or if switching costs are too high.",
                ),
                (
                    "user",
                    f"Persona: {state.target_persona.model_dump()}\nStory: {state.sitemap_and_story.core_story.model_dump()}\n\nFeedback:",
                ),
            ]
        )
        result = (prompt | self.llm).invoke({})
        msg = DialogueMessage(
            role=Role.NEW_EMPLOYEE, content=str(result.content), timestamp=time.time()
        )
        new_history = list(state.debate_history)
        new_history.append(msg)
        return {"debate_history": new_history}


class HackerAgent(BaseAgent):
    """Hacker Agent for 3H Review."""

    def __init__(self, llm: ChatOpenAI, app_settings: Settings | None = None) -> None:
        self.llm = llm
        self.settings = app_settings or get_settings()

    def run(self, state: GlobalState) -> dict[str, Any]:
        if not state.sitemap_and_story:
            return {}
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are the Hacker. Review the wireframe for technical debt, scalability, and security. Avoid unnecessary complexity.",
                ),
                ("user", f"Sitemap: {state.sitemap_and_story.sitemap}\n\nTechnical Review:"),
            ]
        )
        result = (prompt | self.llm).invoke({})
        msg = DialogueMessage(role=Role.FINANCE, content=str(result.content), timestamp=time.time())
        return {"debate_history": [msg]}


class HipsterAgent(BaseAgent):
    """Hipster Agent for 3H Review."""

    def __init__(self, llm: ChatOpenAI, app_settings: Settings | None = None) -> None:
        self.llm = llm
        self.settings = app_settings or get_settings()

    def run(self, state: GlobalState) -> dict[str, Any]:
        if not state.mental_model or not state.sitemap_and_story:
            return {}
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are the Hipster. Review the UX based on 'Don't make me think'. Point out friction against the mental model.",
                ),
                (
                    "user",
                    f"Mental Model: {state.mental_model.model_dump()}\nStory: {state.sitemap_and_story.core_story.model_dump()}\n\nUX Review:",
                ),
            ]
        )
        result = (prompt | self.llm).invoke({})
        msg = DialogueMessage(role=Role.SALES, content=str(result.content), timestamp=time.time())
        return {"debate_history": [msg]}


class HustlerAgent(BaseAgent):
    """Hustler Agent for 3H Review."""

    def __init__(self, llm: ChatOpenAI, app_settings: Settings | None = None) -> None:
        self.llm = llm
        self.settings = app_settings or get_settings()

    def run(self, state: GlobalState) -> dict[str, Any]:
        if not state.alternative_analysis or not state.value_proposition:
            return {}
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are the Hustler. Review the business model unit economics (LTV > 3x CAC). Interrogate who will pay and why.",
                ),
                (
                    "user",
                    f"Alternatives: {state.alternative_analysis.model_dump()}\nVPC: {state.value_proposition.model_dump()}\n\nBusiness Review:",
                ),
            ]
        )
        result = (prompt | self.llm).invoke({})
        msg = DialogueMessage(role=Role.CPO, content=str(result.content), timestamp=time.time())
        return {"debate_history": [msg]}


class OutputGenerationAgent(BaseAgent):
    """Agent for Phase 5 & 6 (Agent Prompt Spec & Experiment Plan)."""

    def __init__(self, llm: ChatOpenAI, app_settings: Settings | None = None) -> None:
        self.llm = llm
        self.settings = app_settings or get_settings()

    def generate_experiment_plan(self, state: GlobalState) -> dict[str, Any]:
        """Generate Experiment Plan."""
        if not state.selected_idea:
            logger.warning("Missing idea for Experiment Plan.")
            return {}

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a growth hacker. Generate an Experiment Plan defining 'What and How to measure' using the MVP.",
                ),
                ("user", f"Idea: {state.selected_idea.title}\n\nGenerate Experiment Plan:"),
            ]
        )
        chain = prompt | self.llm.with_structured_output(ExperimentPlan)
        try:
            result = chain.invoke({})
            if isinstance(result, ExperimentPlan):
                return {"experiment_plan": result}
        except Exception:
            logger.exception("Failed to generate Experiment Plan")
        return {}

    def generate_agent_prompt_spec(self, state: GlobalState) -> dict[str, Any]:
        """Generate Agent Prompt Spec."""
        if not state.sitemap_and_story:
            logger.warning("Missing sitemap for Agent Prompt Spec.")
            return {}

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a Senior Technical Lead. Generate a perfect AgentPromptSpec markdown specification for AI coding tools.",
                ),
                (
                    "user",
                    f"Core Story: {state.sitemap_and_story.core_story.model_dump()}\n\nGenerate Agent Prompt Spec:",
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
        return {}
