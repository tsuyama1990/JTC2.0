from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from src.agents.base import BaseAgent
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.state import GlobalState
from src.tools.search import TavilySearch


class LeanCanvasList(BaseModel):
    """Wrapper for list of Lean Canvases for structured output."""

    canvases: list[LeanCanvas]


class IdeatorAgent(BaseAgent):
    """Agent responsible for generating startup ideas."""

    def __init__(self, llm: ChatOpenAI) -> None:
        self.llm = llm
        self.search_tool = TavilySearch()

    def run(self, state: GlobalState) -> dict[str, Any]:
        """
        Generate 10 Lean Canvas drafts based on the topic.

        Args:
            state: The current global state.

        Returns:
            Updates to the state (generated_ideas).
        """
        topic = state.topic

        # 1. Research
        query = f"emerging business trends and painful problems in {topic}"
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
        # We use with_structured_output to ensure Pydantic validation
        chain = prompt | self.llm.with_structured_output(LeanCanvasList)

        result = chain.invoke({"topic": topic, "research": search_results})

        if not isinstance(result, LeanCanvasList):
            # Fallback or error handling
            return {"generated_ideas": []}

        return {"generated_ideas": result.canvases}
