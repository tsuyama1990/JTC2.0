from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from src.agents.base import BaseAgent
from src.core.config import settings
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.state import GlobalState
from src.tools.search import TavilySearch


class LeanCanvasList(BaseModel):
    """Wrapper for list of Lean Canvases for structured output."""

    canvases: list[LeanCanvas]


class IdeatorAgent(BaseAgent):
    """
    Agent responsible for generating startup ideas based on market research.

    Attributes:
        llm: The Language Model to use for generation.
        search_tool: The tool used for market research.
    """

    def __init__(self, llm: ChatOpenAI) -> None:
        """
        Initialize the Ideator Agent.

        Args:
            llm: A configured ChatOpenAI instance.
        """
        self.llm = llm
        self.search_tool = TavilySearch()

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
        query = settings.search_query_template.format(topic=topic)
        search_results = self.search_tool.search(query)

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
        # Note on Scalability: While generating 10 items is small enough to fit in memory,
        # for larger datasets we would use streaming. Here we adhere to the contract
        # but acknowledge the constraint. The LLM response for 10 items is < 4k tokens.

        chain = prompt | self.llm.with_structured_output(LeanCanvasList)

        try:
            result = chain.invoke({"topic": topic, "research": search_results})
        except Exception:
            # Fallback if LLM fails or structure is invalid
            return {"generated_ideas": []}

        if not isinstance(result, LeanCanvasList):
            return {"generated_ideas": []}

        return {"generated_ideas": result.canvases}
