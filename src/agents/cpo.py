import logging

from langchain_openai import ChatOpenAI

from src.agents.base import SearchTool
from src.agents.personas import PersonaAgent
from src.core.config import Settings
from src.core.nemawashi import NemawashiEngine
from src.data.rag import RAG
from src.domain_models.simulation import Role
from src.domain_models.state import GlobalState

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
        self.nemawashi = NemawashiEngine()

    def _research_impl(self, topic: str) -> str:
        """
        Query the RAG engine for relevant customer insights.
        Overrides the default web search behavior.
        """
        query = f"What do customers say about {topic} or related problems?"
        logger.info(f"CPO querying RAG: {query}")
        return self.rag.query(query)

    def _build_context(self, state: GlobalState) -> str:
        """Add Nemawashi analysis to the context."""
        base_context = super()._build_context(state)

        # Nemawashi Analysis
        try:
            network = state.to_influence_network()
            # Check if network is valid (has stakeholders)
            if not network.stakeholders:
                return base_context

            consensus = self.nemawashi.calculate_consensus(network)
            influencers = self.nemawashi.identify_influencers(network)

            nemawashi_context = (
                f"\n\nPOLITICAL ANALYSIS (Nemawashi):\n"
                f"Consensus Vector (Final Opinions): {consensus}\n"
                f"Key Influencers: {', '.join(influencers)}\n"
            )
            return base_context + nemawashi_context
        except Exception as e:
            logger.warning(f"Nemawashi analysis failed: {e}")
            return base_context
