from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, field_validator

from src.agents.base import BaseAgent, SearchTool
from src.core.config import Settings, settings
from src.core.constants import ERR_UNIQUE_ID_VIOLATION
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.state import GlobalState
from src.tools.search import TavilySearch


class LeanCanvasList(BaseModel):
    """
    Wrapper for list of Lean Canvases for structured output.

    Ensures that generated ideas have unique IDs.
    """

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
        llm: ChatOpenAI,
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
        self.settings = app_settings or settings
        self.search_tool = search_tool or TavilySearch(
            api_key=self.settings.tavily_api_key.get_secret_value()
            if self.settings.tavily_api_key
            else None
        )

    def run(self, state: GlobalState) -> dict[str, Any]:
        """
        Generate 10 Lean Canvas drafts based on the topic.

        This method performs research using Tavily and then uses the LLM
        to generate structured business ideas.

        Args:
            state: The current global state containing the topic.

        Returns:
            A dictionary with state updates (generated_ideas).
        """
        topic = state.topic

        # 1. Research
        # Use configurable template
        query = self.settings.search_query_template.format(topic=topic)
        # Use safe_search for robustness
        search_results = self.search_tool.safe_search(query)

        # 2. Ideation Prompt
        system_prompt = (
            "You are a visionary startup ideator. Your goal is to generate 10 DISTINCT, "
            "viable business ideas based on the provided research.\n"
            "Each idea must be structured as a Lean Canvas.\n"
            "You MUST generate exactly 10 ideas.\n"
            "Assign IDs from 0 to 9 sequentially."
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("user", "Topic: {topic}\n\nResearch Summary:\n{research}"),
            ]
        )

        # 3. Generate
        # We use with_structured_output to ensure Pydantic validation.

        chain = prompt | self.llm.with_structured_output(LeanCanvasList)

        try:
            result = chain.invoke({"topic": topic, "research": search_results})
        except Exception:
            # Fallback if LLM fails or structure is invalid
            # Return empty list to degrade gracefully rather than crashing
            return {"generated_ideas": []}

        if not isinstance(result, LeanCanvasList):
            return {"generated_ideas": []}

        return {"generated_ideas": result.canvases}
