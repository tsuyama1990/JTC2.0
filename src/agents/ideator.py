import logging
from typing import Any

from pydantic import BaseModel, Field
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.agents.base import BaseAgent, SearchTool
from src.core.config import get_settings
from src.core.interfaces import ILLMClient
from src.core.llm import get_llm
from src.domain_models.common import LazyIdeaIterator
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.state import GlobalState
from src.tools.search import TavilySearch

logger = logging.getLogger(__name__)


class IdeasResponse(BaseModel):
    """Schema to enforce LLM output format."""

    ideas: list[LeanCanvas] = Field(..., description="Exactly 10 Lean Canvas draft objects.")


class IdeaGenerator:
    """Service class responsible for interacting with the LLM to generate ideas."""

    def __init__(self, llm: ILLMClient | None = None) -> None:
        self.llm = llm or get_llm()

    @retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def generate(self, topic: str, search_results: str) -> list[LeanCanvas]:
        """Generate ideas using the LLM with retry logic."""
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
            ("system", system_prompt),
            ("human", human_prompt),
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


class TopicInput(BaseModel):
    """Schema to enforce semantic validation of the input topic before research."""

    topic: str = Field(
        ...,
        min_length=3,
        max_length=200,
        pattern=r"^[a-zA-Z0-9\s\-_]+$",
        description="A clean, alphanumeric business topic.",
    )


class IdeatorAgent(BaseAgent):
    """
    Ideator Agent responsible for generating initial startup ideas.
    Phase 1: Idea Verification.
    """

    def __init__(
        self, llm: ILLMClient | None = None, search_tool: SearchTool | None = None
    ) -> None:
        """
        Initialize the Ideator Agent.

        Args:
            llm: Optional language model override for testing.
            search_tool: Optional search tool override for testing.
        """
        self.llm = llm or get_llm()
        self.search_tool = search_tool or TavilySearch()
        self.generator = IdeaGenerator(llm=self.llm)

    def run(self, state: GlobalState) -> dict[str, Any]:
        """Alias for execute to align with BaseAgent abstract method."""
        return {"generated_ideas": self.execute(state).generated_ideas}

    def _research(self, topic: str) -> str:
        """Execute research logic using validated input to prevent prompt injections."""
        try:
            # Semantic validation: Ensure format and length constraints
            validated_topic = TopicInput(topic=topic).topic
        except Exception:
            logger.exception("Invalid topic format for research")
            return "No research data available due to invalid topic input."

        settings = get_settings()
        # Securely escape the template by avoiding generic .format()
        # which can execute arbitrary formatting logic if the template is compromised.
        # Ensure we only replace the exact placeholder literal safely.
        template = settings.search_query_template
        query = template.replace("{topic}", validated_topic)
        return self.search_tool.safe_search(query)

    def execute(self, state: GlobalState) -> GlobalState:
        """
        Execute the Ideator logic.
        """
        logger.info(f"IdeatorAgent starting for topic: {state.topic}")

        search_results = self._research(state.topic)

        try:
            ideas = self.generator.generate(state.topic, search_results)
            state.generated_ideas = LazyIdeaIterator(iter(ideas))
        except Exception:
            logger.exception("Failed to generate ideas")
            state.generated_ideas = LazyIdeaIterator(iter([]))
        else:
            logger.info("Successfully generated 10 Lean Canvas drafts.")

        return state
