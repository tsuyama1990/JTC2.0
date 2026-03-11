import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from src.agents.base import BaseAgent, SearchTool
from src.core.config import get_settings
from src.core.llm import get_llm
from src.domain_models.common import LazyIdeaIterator
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.state import GlobalState
from src.tools.search import TavilySearch

logger = logging.getLogger(__name__)


class IdeasResponse(BaseModel):
    """Schema to enforce LLM output format."""

    ideas: list[LeanCanvas] = Field(..., description="Exactly 10 Lean Canvas draft objects.")


class IdeatorAgent(BaseAgent):
    """
    Ideator Agent responsible for generating initial startup ideas.
    Phase 1: Idea Verification.
    """

    def __init__(self, llm: Any = None, search_tool: SearchTool | None = None) -> None:
        """
        Initialize the Ideator Agent.

        Args:
            llm: Optional language model override for testing.
            search_tool: Optional search tool override for testing.
        """
        self.llm = llm or get_llm()
        self.search_tool = search_tool or TavilySearch()

    def run(self, state: GlobalState) -> dict[str, Any]:
        """Alias for execute to align with BaseAgent abstract method."""
        return {"generated_ideas": self.execute(state).generated_ideas}

    def _research(self, topic: str) -> str:
        """Execute research logic."""
        settings = get_settings()
        query = settings.search_query_template.format(topic=topic)
        return self.search_tool.safe_search(query)

    def _generate_ideas(self, topic: str, search_results: str) -> list[LeanCanvas]:
        """Generate ideas logic separated for testing."""
        system_prompt = (
            "You are an expert Startup Ideator and Business Strategist. "
            "Your objective is to generate exactly 10 distinct, 'Good Crazy' business ideas "
            "based on the provided topic and macro-environment (PEST) search results. "
            "You MUST output exactly 10 ideas, formatted strictly according to the requested JSON schema. "
            "Each idea must be creative, solve a real problem, and provide a 10x unique value proposition."
        )

        human_prompt = (
            f"Topic: {topic}\n\n"
            f"Market Context (Search Results):\n{search_results}\n\n"
            "Generate exactly 10 Lean Canvas drafts."
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]

        structured_llm = self.llm.with_structured_output(IdeasResponse)
        response = structured_llm.invoke(messages)

        if hasattr(response, "ideas"):
            ideas = response.ideas
        elif isinstance(response, dict):
            ideas = response.get("ideas", [])
        else:
            ideas = []

        for idx, idea in enumerate(ideas):
            idea.id = idx

        ideas = ideas[:10]

        while len(ideas) < 10:
            idx = len(ideas)
            ideas.append(
                LeanCanvas(
                    id=idx,
                    title=f"Fallback Idea {idx}",
                    problem="Fallback Problem",
                    customer_segments="Fallback Segments",
                    unique_value_prop="Fallback UVP",
                    solution="Fallback Solution",
                )
            )

        return list(ideas)

    def execute(self, state: GlobalState) -> GlobalState:
        """
        Execute the Ideator logic.
        """
        logger.info(f"IdeatorAgent starting for topic: {state.topic}")

        search_results = self._research(state.topic)

        try:
            ideas = self._generate_ideas(state.topic, search_results)
            state.generated_ideas = LazyIdeaIterator(iter(ideas))
        except Exception:
            logger.exception("Failed to generate ideas")
            state.generated_ideas = LazyIdeaIterator(iter([]))
        else:
            logger.info("Successfully generated 10 Lean Canvas drafts.")

        return state
