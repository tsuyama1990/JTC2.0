import logging
import time
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic_core import ValidationError as PydanticValidationError
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.agents.base import BaseAgent, SearchTool
from src.core.config import Settings, get_settings
from src.domain_models.alternative_analysis import AlternativeAnalysis
from src.domain_models.persona import Persona
from src.domain_models.simulation import DialogueMessage, Role
from src.domain_models.state import GlobalState
from src.domain_models.value_proposition_canvas import ValuePropositionCanvas
from src.tools.search import TavilySearch

logger = logging.getLogger(__name__)


class RateLimiter:
    """Class to manage API rate limiting via composition instead of multiple inheritance."""
    def __init__(self, min_request_interval: float = 1.0) -> None:
        self._last_request_time: float = 0.0
        self._min_request_interval: float = min_request_interval

    def wait(self) -> None:
        """Enforce rate limiting for API calls."""
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()


class PersonaGeneratorAgent(BaseAgent):
    """
    Agent responsible for Phase 2, Step 2: Persona & Empathy Mapping.
    Generates a high-resolution Persona and EmpathyMap based on the selected idea.
    """

    def __init__(self, llm: ChatOpenAI | Any) -> None:
        self.llm = llm

    def run(self, state: GlobalState) -> dict[str, Any]:
        """Execute the Persona Generation logic."""
        if not state.selected_idea:
            logger.warning("No selected idea found for Persona Generation.")
            return {}

        system_prompt = (
            "You are an expert UX Researcher and Product Strategist. "
            "Your task is to generate a highly detailed, realistic Customer Persona and an Empathy Map "
            "(Says, Thinks, Does, Feels) based on the provided business idea. "
            "Ensure the output strictly adheres to the requested JSON schema and avoid hallucinations."
        )
        human_prompt = (
            f"Business Idea: {state.selected_idea.title}\n"
            f"Problem: {state.selected_idea.problem}\n"
            f"Solution: {state.selected_idea.solution}\n"
            f"Customer Segments: {state.selected_idea.customer_segments}\n\n"
            "Generate the Persona with Empathy Map."
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]

        try:
            persona = self._invoke_llm(messages)
        except Exception:
            logger.exception("Failed to generate Persona after retries")
            return {}
        else:
            return {"target_persona": persona}

    @retry(
        retry=retry_if_exception_type((ValueError, TypeError, KeyError, PydanticValidationError)),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def _invoke_llm(self, messages: list[Any]) -> Persona:
        structured_llm = self.llm.with_structured_output(Persona)
        result = structured_llm.invoke(messages)
        if isinstance(result, dict):
            result = Persona.model_validate(result)
        return result


class AlternativeAnalysisAgent(BaseAgent):
    """
    Agent responsible for Phase 2, Step 3: Alternative Analysis.
    Identifies current alternatives and infers the 10x value.
    """

    def __init__(self, llm: ChatOpenAI | Any) -> None:
        self.llm = llm

    def run(self, state: GlobalState) -> dict[str, Any]:
        if not state.selected_idea or not state.target_persona:
            logger.warning("Missing selected idea or persona for Alternative Analysis.")
            return {}

        system_prompt = (
            "You are a sharp Business Analyst. Your task is to perform an Alternative Analysis. "
            "Identify the current alternative tools (e.g., Excel, manual work, existing SaaS) "
            "the persona uses, determine the switching costs, and articulate the 10x value proposition "
            "that would compel them to switch to our new solution. "
            "Output must strictly match the required JSON schema."
        )
        human_prompt = (
            f"Idea: {state.selected_idea.title} - {state.selected_idea.solution}\n"
            f"Target Persona: {state.target_persona.name}, {state.target_persona.occupation}\n"
            f"Persona Goals: {', '.join(state.target_persona.goals)}\n"
            f"Persona Frustrations: {', '.join(state.target_persona.frustrations)}\n\n"
            "Generate the Alternative Analysis."
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]

        try:
            analysis = self._invoke_llm(messages)
        except Exception:
            logger.exception("Failed to generate Alternative Analysis after retries")
            return {}
        else:
            return {"alternative_analysis": analysis}

    @retry(
        retry=retry_if_exception_type((ValueError, TypeError, KeyError, PydanticValidationError)),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def _invoke_llm(self, messages: list[Any]) -> AlternativeAnalysis:
        structured_llm = self.llm.with_structured_output(AlternativeAnalysis)
        result = structured_llm.invoke(messages)
        if isinstance(result, dict):
            result = AlternativeAnalysis.model_validate(result)
        return result


class ValuePropositionAgent(BaseAgent):
    """
    Agent responsible for Phase 2, Step 4: Value Proposition Design.
    """

    def __init__(self, llm: ChatOpenAI | Any) -> None:
        self.llm = llm

    def run(self, state: GlobalState) -> dict[str, Any]:
        if not state.selected_idea or not state.target_persona:
            logger.warning("Missing required context for Value Proposition Design.")
            return {}

        system_prompt = (
            "You are an expert Product Manager. Your task is to generate a Value Proposition Canvas. "
            "Based on the provided persona and alternative analysis, map the Customer Profile (Jobs, Pains, Gains) "
            "to the Value Map (Products & Services, Pain Relievers, Gain Creators). "
            "Finally, evaluate how well they fit. "
            "Output must strictly match the required JSON schema."
        )

        alt_analysis_text = ""
        if state.alternative_analysis:
            alt_analysis_text = f"Alternative Analysis: Switching Cost: {state.alternative_analysis.switching_cost}, 10x Value: {state.alternative_analysis.ten_x_value}\n"

        human_prompt = (
            f"Idea: {state.selected_idea.title}\n"
            f"Solution: {state.selected_idea.solution}\n"
            f"Target Persona: {state.target_persona.name}, {state.target_persona.occupation}\n"
            f"Persona Frustrations (Pains to solve): {', '.join(state.target_persona.frustrations)}\n"
            f"{alt_analysis_text}\n"
            "Generate the Value Proposition Canvas."
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]

        try:
            vpc = self._invoke_llm(messages)
        except Exception:
            logger.exception("Failed to generate Value Proposition Canvas after retries")
            return {}
        else:
            return {"value_proposition_canvas": vpc}

    @retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def _invoke_llm(self, messages: list[Any]) -> ValuePropositionCanvas:
        structured_llm = self.llm.with_structured_output(ValuePropositionCanvas)
        result = structured_llm.invoke(messages)
        if isinstance(result, dict):
            result = ValuePropositionCanvas.model_validate(result)
        return result


class PersonaAgent(BaseAgent):
    """Base class for persona-based agents in the simulation."""

    def __init__(
        self,
        llm: ChatOpenAI,
        role: Role,
        system_prompt: str,
        search_tool: SearchTool | None = None,
        app_settings: Settings | None = None,
    ) -> None:
        self.llm = llm
        self.role = role
        self.system_prompt = system_prompt
        self.settings = app_settings or get_settings()
        self.rate_limiter = RateLimiter()

        self.search_tool = search_tool or TavilySearch(
            api_key=self.settings.tavily_api_key.get_secret_value()
            if self.settings.tavily_api_key
            else None
        )
        self._research_cache: dict[str, str] = {}

    def _build_context(self, state: GlobalState) -> str:
        """Construct the conversation history context."""
        context_parts = ["\nDEBATE HISTORY:"]

        if state.selected_idea:
            # Efficient prepending logic or just standard order
            context_parts.insert(0, f"UVP: {state.selected_idea.unique_value_prop}")
            context_parts.insert(0, f"SOLUTION: {state.selected_idea.solution}")
            context_parts.insert(0, f"PROBLEM: {state.selected_idea.problem}")
            context_parts.insert(0, f"IDEA: {state.selected_idea.title}")

        # Generator expression for history
        context_parts.extend(f"{msg.role}: {msg.content}" for msg in state.debate_history)

        return "\n".join(context_parts)

    def _generate_response(self, context: str, research_data: str = "") -> str:
        """Generate response using LLM."""
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                (
                    "user",
                    f"Context:\n{context}\n\nResearch Data:\n{research_data}\n\nYour turn to speak:",
                ),
            ]
        )
        chain = prompt | self.llm
        response = chain.invoke({})
        return str(response.content)

    def _cached_research(self, topic: str) -> str:
        """Cache research results to avoid redundant API calls."""
        if topic in self._research_cache:
            return self._research_cache[topic]

        # But we still need to know if _research_impl exists on the subclass
        if hasattr(self, "_research_impl"):
            try:
                self.rate_limiter.wait()
                # Ensure return type is str
                # We use getattr to bypass mypy 'attr-defined' error for dynamic dispatch
                impl = self._research_impl
                result: str = impl(topic)
            except Exception as e:
                logger.error(f"Research implementation failed for {topic}: {e}", exc_info=True)
                return ""
            else:
                self._research_cache[topic] = result
                return result

        logger.warning(f"Agent {self.role} attempted research without implementation.")
        return ""

    def run(self, state: GlobalState) -> dict[str, Any]:
        """Run the agent logic."""
        context = self._build_context(state)
        research_data = ""

        # Override in subclasses if research is needed
        if hasattr(self, "_research_impl") and state.selected_idea:
            title = state.selected_idea.title
            logger.debug(f"Agent {self.role} executing research on: {title}")
            # Use the cached wrapper
            research_data = self._cached_research(title)

        content = self._generate_response(context, research_data)
        logger.debug(f"Agent {self.role} generated response: {content[:50]}...")

        message = DialogueMessage(role=self.role, content=content, timestamp=time.time())

        # Return state update.
        # Note: LangGraph usually appends to list if configured with reducer,
        # but here GlobalState uses list replacement by default in Pydantic.
        # We need to append.

        new_history = [*list(state.debate_history), message]
        return {"debate_history": new_history}


class FinanceAgent(PersonaAgent):
    """The skeptical Finance Manager."""

    def __init__(
        self,
        llm: ChatOpenAI,
        search_tool: SearchTool | None = None,
        app_settings: Settings | None = None,
    ) -> None:
        system_prompt = (
            "You are a conservative Finance Manager at a large Japanese traditional company. "
            "You always ask about cost, risk, and timeline. "
            "You use market data to find reasons why new ideas will fail. "
            "Be critical but professional."
        )
        super().__init__(llm, Role.FINANCE, system_prompt, search_tool, app_settings)

    def _research_impl(self, topic: str) -> str:
        """Perform market research on risks."""
        query = f"market risks and costs for {topic}"
        return self.search_tool.safe_search(query)


class SalesAgent(PersonaAgent):
    """The aggressive Sales Manager."""

    def __init__(
        self,
        llm: ChatOpenAI,
        search_tool: SearchTool | None = None,
        app_settings: Settings | None = None,
    ) -> None:
        system_prompt = (
            "You are an aggressive Sales Manager. "
            "You worry about cannibalizing existing products and whether the sales force can actually sell this. "
            "You care about immediate revenue and customer trust."
        )
        super().__init__(llm, Role.SALES, system_prompt, search_tool, app_settings)


class NewEmployeeAgent(PersonaAgent):
    """The proxy for the user."""

    def __init__(
        self,
        llm: ChatOpenAI,
        search_tool: SearchTool | None = None,
        app_settings: Settings | None = None,
    ) -> None:
        system_prompt = (
            "You are a new employee presenting a startup idea. "
            "You are nervous. You try to answer questions but often falter. "
            "You defend the idea passionately but acknowledge weaknesses."
        )
        super().__init__(llm, Role.NEW_EMPLOYEE, system_prompt, search_tool, app_settings)
