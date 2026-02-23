import logging

from langchain_openai import ChatOpenAI

from src.agents.base import SearchTool
from src.agents.personas import PersonaAgent
from src.core.config import Settings
from src.data.rag import RAG
from src.domain_models.simulation import Role

logger = logging.getLogger(__name__)


class CPOAgent(PersonaAgent):
    """
    The Chief Product Officer (CPO) Agent.

    Acts as a mentor who provides fact-based advice using the RAG engine
    to validate or invalidate assumptions based on customer transcripts.
    """

    def __init__(
        self,
        llm: ChatOpenAI,
        search_tool: SearchTool | None = None,
        app_settings: Settings | None = None,
        rag_path: str = "./vector_store",
    ) -> None:
        system_prompt = (
            "You are the Chief Product Officer (CPO). "
            "You are a mentor to the New Employee. "
            "You do not speak in the main meeting. "
            "In the rooftop phase, you provide fact-based advice using customer data. "
            "You ignore opinions and focus on evidence from transcripts. "
            "Use the provided research data (from RAG) to find contradictions "
            "between the Plan and the Customer Interview."
        )
        super().__init__(llm, Role.CPO, system_prompt, search_tool, app_settings)
        self.rag = RAG(persist_dir=rag_path)

    def _research_impl(self, topic: str) -> str:
        """
        Query the RAG engine for relevant customer insights.
        Overrides the default web search behavior.
        """
        query = f"What do customers say about {topic} or related problems?"
        logger.info(f"CPO querying RAG: {query}")
        return self.rag.query(query)
