import logging
import time
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from src.agents.base import SearchTool
from src.agents.personas import PersonaAgent
from src.core.config import Settings
from src.data.rag import RAG
from src.domain_models.simulation import DialogueMessage, Role
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
        llm: BaseChatModel,
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

        # Security: Validate RAG path against allowed config securely
        from pathlib import Path

        is_allowed = False
        resolved_actual = Path(actual_rag_path).resolve(strict=False)

        for allowed_path in self.settings.rag_allowed_paths:
            resolved_allowed = Path(allowed_path).resolve(strict=False)
            try:
                resolved_actual.relative_to(resolved_allowed)
                is_allowed = True
                break
            except ValueError:
                continue

        if not is_allowed:
            msg = f"Invalid RAG path '{actual_rag_path}'. Must be within allowed paths: {self.settings.rag_allowed_paths}"
            raise ValueError(msg)

        self.rag = RAG(persist_dir=actual_rag_path)

    def _cached_research(self, query: str) -> str:
        """
        Query the RAG engine for relevant customer insights and cache it.
        Overrides the default web search behavior.
        """
        if query in self._research_cache:
            return self._research_cache[query]

        try:
            logger.info(f"CPO querying RAG: {query}")
            result: str = self.rag.query(query)
        except Exception:
            logger.exception("Error querying RAG")
            return "No customer insights available due to error."
        else:
            self._research_cache[query] = result
            return result

    def run(self, state: GlobalState) -> dict[str, Any]:
        """
        Run the CPO agent logic with Nemawashi context.
        """
        try:
            # 1. Build Standard Context
            context = self._build_context(state)

            # 2. Get Research Data (RAG)
            research_data = ""

            # If transcripts exist, we use them as context
            transcript_context = ""
            if state.transcripts:
                transcript_context = "against customer interviews"
            else:
                transcript_context = "against general knowledge"

            if state.selected_idea:
                base_query = f"Validate assumption: {state.selected_idea.title} {transcript_context}"
                research_data += self._cached_research(base_query)

            # 3. Inject Nemawashi (Influence) Data
            if state.influence_network:
                stakeholders_info = ["\nSTAKEHOLDER ANALYSIS (Nemawashi):"]
                for s in state.influence_network.stakeholders:
                    status = (
                        "Supportive"
                        if s.initial_support > 0.7
                        else "Resistant"
                        if s.initial_support < 0.3
                        else "Neutral"
                    )
                    stakeholders_info.append(
                        f"- {s.name}: {status} (Support={s.initial_support:.2f}, Stubbornness={s.stubbornness:.2f})"
                    )

                research_data += "\n".join(stakeholders_info)

            # 4. Inject Value Proposition Canvas and Alternative Analysis
            if state.vpc:
                vpc_json = state.vpc.model_dump_json()
                vpc_query = f"Validate VPC: {vpc_json} against customer needs"
                vpc_validation = self._cached_research(vpc_query)
                research_data += f"\n\nVALUE PROPOSITION CANVAS VALIDATION:\n{vpc_validation}"

            if state.alternative_analysis:
                alt_json = state.alternative_analysis.model_dump_json()
                alt_query = f"Validate alternative analysis: {alt_json} against customer alternatives"
                alt_validation = self._cached_research(alt_query)
                research_data += f"\n\nALTERNATIVE ANALYSIS VALIDATION:\n{alt_validation}"

            content = self._generate_response(context, research_data)

            # Create message
            message = DialogueMessage(role=self.role, content=content, timestamp=time.time())

        except Exception as e:
            logger.exception("Error in CPO Agent Run")
            return {
                "error": f"RAG query failed or CPO error: {e}",
                "debate_history": list(state.debate_history)
            }
        else:
            # Construct new history
            new_history = [*list(state.debate_history), message]
            return {"debate_history": new_history}
