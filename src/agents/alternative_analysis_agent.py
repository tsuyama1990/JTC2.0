import logging
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.agents.base import BaseAgent
from src.domain_models.alternative_analysis import AlternativeAnalysis
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


class AlternativeAnalysisAgent(BaseAgent):
    """Generates AlternativeAnalysis based on the selected idea and persona."""

    def __init__(self, llm: ChatOpenAI) -> None:
        self.llm = llm

    def run(self, state: GlobalState) -> dict[str, Any]:
        """Generate AlternativeAnalysis."""
        if not state.selected_idea:
            logger.warning("No selected idea for AlternativeAnalysis generation.")
            return {}

        if not state.target_persona:
            logger.warning("No target persona for AlternativeAnalysis generation.")
            return {}

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert business strategist. Create an AlternativeAnalysis based on the provided business idea context and target persona. Focus on current alternatives and switching costs. The output must strictly follow the required schema without any hallucination.",
                ),
                (
                    "user",
                    f"Idea Title: {state.selected_idea.title}\n"
                    f"Problem: {state.selected_idea.problem}\n"
                    f"Target Persona: {state.target_persona.name} ({state.target_persona.occupation})\n"
                    f"Unique Value Proposition: {state.selected_idea.unique_value_prop}\n"
                    f"Solution: {state.selected_idea.solution}\n\n"
                    "Generate the AlternativeAnalysis.",
                ),
            ]
        )
        chain = prompt | self.llm.with_structured_output(AlternativeAnalysis)
        try:
            result = chain.invoke({})
            if isinstance(result, AlternativeAnalysis):
                return {"alternative_analysis": result}
        except Exception:
            logger.exception("Failed to generate AlternativeAnalysis")

        return {}
