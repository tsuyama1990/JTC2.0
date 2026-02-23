import logging
from typing import Any

from langchain_openai import ChatOpenAI

from src.agents.base import SearchTool
from src.agents.personas import PersonaAgent
from src.core.config import Settings
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
        rag_path: str | None = None,
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

        # Use provided path or fallback to settings (not hardcoded string)
        actual_rag_path = rag_path or self.settings.rag_persist_dir
        self.rag = RAG(persist_dir=actual_rag_path)

    def _research_impl(self, topic: str) -> str:
        """
        Query the RAG engine for relevant customer insights.
        Overrides the default web search behavior.
        """
        query = f"What do customers say about {topic} or related problems?"
        logger.info(f"CPO querying RAG: {query}")
        return self.rag.query(query)

    def run(self, state: GlobalState) -> dict[str, Any]:
        """
        Run the CPO agent logic with Nemawashi context.
        """
        # 1. Build Standard Context
        context = self._build_context(state)

        # 2. Get Research Data (RAG)
        research_data = ""
        if state.selected_idea:
            research_data = self._cached_research(state.selected_idea.title)

        # 3. Inject Nemawashi (Influence) Data
        if state.influence_network:
            # Check for consensus data which might be injected by the Nemawashi engine node
            # The node calculates consensus and updates support levels.

            # We provide a summary of the political landscape.
            # Ideally, we would use the Engine here to get fresh analytics, but to avoid
            # heavy computation inside the agent, we rely on the state being up to date.

            stakeholders_info = ["\nSTAKEHOLDER ANALYSIS (Nemawashi):"]
            for s in state.influence_network.stakeholders:
                status = "Supportive" if s.initial_support > 0.7 else "Resistant" if s.initial_support < 0.3 else "Neutral"
                stakeholders_info.append(
                    f"- {s.name}: {status} (Support={s.initial_support:.2f}, Stubbornness={s.stubbornness:.2f})"
                )

            research_data += "\n".join(stakeholders_info)

        content = self._generate_response(context, research_data)

        # CPO doesn't speak in the debate history usually?
        # The prompt says "In the rooftop phase... provide advice".
        # So we return the message.
        # But wait, does CPO output go to debate_history?
        # The graph wrapper `safe_cpo_run` returns it.
        # If we append to debate_history, it shows up as a message.

        # We return the standard dict update.
        import time

        from src.domain_models.simulation import DialogueMessage

        message = DialogueMessage(role=self.role, content=content, timestamp=time.time())
        new_history = [*list(state.debate_history), message]
        return {"debate_history": new_history}
