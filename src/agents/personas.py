import logging
import time
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.agents.base import BaseAgent, SearchTool
from src.core.config import Settings, get_settings
from src.domain_models.simulation import DialogueMessage, Role
from src.domain_models.state import GlobalState
from src.tools.search import TavilySearch

logger = logging.getLogger(__name__)


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

        # Ensure API keys are present if we are initializing default tools
        if search_tool is None:
            self.settings.validate_api_keys()

        self.search_tool = search_tool or TavilySearch(
            api_key=self.settings.tavily_api_key.get_secret_value()
            if self.settings.tavily_api_key
            else None
        )

    def _build_context(self, state: GlobalState) -> str:
        """Construct the conversation history context."""
        context = []
        if state.selected_idea:
            # Pre-allocate list for efficiency, though append is O(1)
            context = [
                f"IDEA: {state.selected_idea.title}",
                f"PROBLEM: {state.selected_idea.problem}",
                f"SOLUTION: {state.selected_idea.solution}",
                f"UVP: {state.selected_idea.unique_value_prop}",
                "\nDEBATE HISTORY:"
            ]
        else:
            context = ["\nDEBATE HISTORY:"]

        # Efficiently extend the list
        context.extend(f"{msg.role}: {msg.content}" for msg in state.debate_history)

        return "\n".join(context)

    def _generate_response(self, context: str, research_data: str = "") -> str:
        """Generate response using LLM."""
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", self.system_prompt),
                ("user", f"Context:\n{context}\n\nResearch Data:\n{research_data}\n\nYour turn to speak:"),
            ]
        )
        chain = prompt | self.llm
        response = chain.invoke({})
        return str(response.content)

    def run(self, state: GlobalState) -> dict[str, Any]:
        """Run the agent logic."""
        context = self._build_context(state)
        research_data = ""

        # Override in subclasses if research is needed
        if hasattr(self, "_research") and state.selected_idea:
             title = state.selected_idea.title
             logger.debug(f"Agent {self.role} executing research on: {title}")
             research_data = self._research(title)

        content = self._generate_response(context, research_data)
        logger.debug(f"Agent {self.role} generated response: {content[:50]}...")

        message = DialogueMessage(
            role=self.role,
            content=content,
            timestamp=time.time()
        )

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
        super().__init__(
            llm, Role.FINANCE, system_prompt, search_tool, app_settings
        )

    def _research(self, topic: str) -> str:
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
        super().__init__(
            llm, Role.SALES, system_prompt, search_tool, app_settings
        )


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
        super().__init__(
            llm, Role.NEW_EMPLOYEE, system_prompt, search_tool, app_settings
        )


class CPOAgent(PersonaAgent):
    """The silent Mentor CPO."""

    def __init__(
        self,
        llm: ChatOpenAI,
        search_tool: SearchTool | None = None,
        app_settings: Settings | None = None,
    ) -> None:
        system_prompt = (
            "You are the Chief Product Officer (CPO). "
            "You are a mentor to the New Employee. "
            "You do not speak in the main meeting. "
            "In the rooftop phase, you provide fact-based advice using market data. "
            "You never give the final answer, but provide 'weapons' (facts/examples) to help them win the argument."
        )
        super().__init__(
            llm, Role.CPO, system_prompt, search_tool, app_settings
        )

    def _research(self, topic: str) -> str:
        """Perform deep market research for mentoring."""
        query = f"successful business models and case studies similar to {topic}"
        return self.search_tool.safe_search(query)
