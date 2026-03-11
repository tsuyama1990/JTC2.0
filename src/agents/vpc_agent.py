import logging
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.agents.base import BaseAgent
from src.domain_models.state import GlobalState
from src.domain_models.value_proposition import ValuePropositionCanvas

logger = logging.getLogger(__name__)


class VPCAgent(BaseAgent):
    """Generates ValuePropositionCanvas based on the selected idea, persona and alternative analysis."""

    def __init__(self, llm: ChatOpenAI) -> None:
        self.llm = llm

    def run(self, state: GlobalState) -> dict[str, Any]:
        """Generate Value Proposition Canvas."""
        if not state.selected_idea:
            logger.warning("No selected idea for ValuePropositionCanvas generation.")
            return {}

        if not state.target_persona:
            logger.warning("No target persona for ValuePropositionCanvas generation.")
            return {}

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert product manager. Create a ValuePropositionCanvas based on the provided business idea context and target persona. The output must strictly follow the required schema without any hallucination.",
                ),
                (
                    "user",
                    f"Idea Title: {state.selected_idea.title}\n"
                    f"Problem: {state.selected_idea.problem}\n"
                    f"Target Persona: {state.target_persona.name} ({state.target_persona.occupation})\n"
                    f"Target Persona Goals: {', '.join(state.target_persona.goals)}\n"
                    f"Unique Value Proposition: {state.selected_idea.unique_value_prop}\n"
                    f"Solution: {state.selected_idea.solution}\n\n"
                    "Generate the ValuePropositionCanvas.",
                ),
            ]
        )
        chain = prompt | self.llm.with_structured_output(ValuePropositionCanvas)
        try:
            result = chain.invoke({})
            if isinstance(result, ValuePropositionCanvas):
                return {"value_proposition_canvas": result}
        except Exception:
            logger.exception("Failed to generate ValuePropositionCanvas")

        return {}
