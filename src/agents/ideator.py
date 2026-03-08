from collections.abc import Iterator
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from src.agents.base import BaseAgent, SearchTool
from src.core.config import Settings, get_settings
from src.core.constants import ERR_UNIQUE_ID_VIOLATION
from src.core.interfaces import LLMInterface
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.state import GlobalState
from src.tools.search import TavilySearch


class LeanCanvasList(BaseModel):
    """
    Wrapper for list of Lean Canvases for structured output.

    Ensures that generated ideas have unique IDs.
    """

    model_config = ConfigDict(extra="forbid")

    canvases: list[LeanCanvas]

    @field_validator("canvases")
    @classmethod
    def validate_unique_ids(cls, v: list[LeanCanvas]) -> list[LeanCanvas]:
        """Ensure all generated canvases have unique IDs."""
        ids = [canvas.id for canvas in v]
        if len(ids) != len(set(ids)):
            raise ValueError(ERR_UNIQUE_ID_VIOLATION)
        return v


class IdeatorAgent(BaseAgent):
    """
    Agent responsible for generating startup ideas based on market research.

    Attributes:
        llm: The Language Model to use for generation.
        search_tool: The tool used for market research.
        settings: Application settings.
    """

    def __init__(
        self,
        llm: LLMInterface,
        search_tool: SearchTool | None = None,
        app_settings: Settings | None = None,
    ) -> None:
        """
        Initialize the Ideator Agent.

        Args:
            llm: A configured ChatOpenAI instance.
            search_tool: Optional search tool instance (Dependency Injection).
            app_settings: Optional settings override (Dependency Injection).
        """
        self.llm = llm
        self.settings = app_settings or get_settings()
        self.search_tool = search_tool or TavilySearch(
            api_key=self.settings.tavily_api_key.get_secret_value()
            if self.settings.tavily_api_key
            else None
        )

    def _research(self, topic: str) -> str:
        """Perform market research using the search tool."""
        query = self.settings.search_query_template.format(topic=topic)
        return self.search_tool.safe_search(query)

    def _generate_ideas(self, topic: str, research_data: str) -> Iterator[LeanCanvas]:
        """
        Invoke LLM to generate ideas and yield them as an iterator.
        """
        system_message = (
            "You are a visionary startup ideator. Your goal is to generate 10 DISTINCT, "
            "viable business ideas based on the provided research.\n"
            "Each idea must be structured as a Lean Canvas.\n"
            "You MUST generate exactly 10 ideas.\n"
            "Assign IDs from 0 to 9 sequentially."
        )
        prompt = f"Topic: {topic}\n\nResearch Summary:\n{research_data}"

        try:
            result = self.llm.generate_structured(
                prompt=prompt, schema=LeanCanvasList, system_message=system_message
            )
        except Exception:
            return

        if not isinstance(result, LeanCanvasList):
            return

        yield from result.canvases

    def run(self, state: GlobalState) -> dict[str, Any]:
        """
        Generate 10 Lean Canvas drafts based on the topic.
        """
        topic = state.topic

        # 1. Research
        search_results = self._research(topic)

        # 2. Generate
        ideas_iter = self._generate_ideas(topic, search_results)

        return {"generated_ideas": ideas_iter}
