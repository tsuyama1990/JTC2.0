import logging
import time
from typing import Any

from src.agents.base import BaseAgent
from src.core.config import Settings, get_settings
from src.core.interfaces import LLMClient, RAGInterface
from src.domain_models.simulation import DialogueMessage, Role
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


class CPOAgent(BaseAgent):
    """
    The Chief Product Officer (CPO) Agent.
    Makes the final decision based on debate history, stakeholder dynamics,
    and RAG context.
    """

    def __init__(
        self,
        llm: LLMClient,
        rag: RAGInterface,
        app_settings: Settings | None = None,
        rag_path: str | None = None,
    ) -> None:
        self.llm = llm
        self.role = Role.CPO
        self.settings = app_settings or get_settings()
        self.rag = rag

        # Basic persona prompt
        self.system_prompt = (
            "You are the CPO. Your role is to finalize the decision based on the debate. "
            "You consider the new employee's passion, but also heed the warnings of Sales and Finance. "
            "You MUST query your internal knowledge base (RAG) before making a decision. "
            "You can choose to 'Approve', 'Reject', or 'Request Pivot'."
        )

    def _build_context(self, state: GlobalState) -> str:
        """Construct the conversation history context."""
        context_parts = ["\nDEBATE HISTORY:"]

        if state.selected_idea:
            context_parts.insert(0, f"IDEA: {state.selected_idea.title}")

        # Generator expression for history
        context_parts.extend(f"{msg.role}: {msg.content}" for msg in state.debate_history)

        return "\n".join(context_parts)

    def _generate_response(self, context: str, research_data: str) -> str:
        """Generate final decision using LLM."""
        prompt = [
            ("system", self.system_prompt),
            (
                "user",
                f"Context:\n{context}\n\nStakeholder & RAG Data:\n{research_data}\n\nYour final decision:",
            ),
        ]
        response = self.llm.invoke(prompt)
        return str(response.content)

    def run(self, state: GlobalState) -> dict[str, Any]:
        """
        Run the CPO agent logic.
        Incorporates RAG querying and simulation logic (Nemawashi).
        """
        try:
            context = self._build_context(state)
            research_data = ""

            # 1. Query RAG for precedent
            if state.selected_idea:
                query = f"Past decisions regarding {state.selected_idea.title} or similar ideas."
                rag_result = self.rag.query(query)
                research_data += f"\nINTERNAL RAG PRECEDENT:\n{rag_result}\n"

            # 2. Inject Nemawashi (Stakeholder) context if available
            if getattr(state, "simulation_data", None) and getattr(
                getattr(state, "simulation_data", None), "stakeholders", None
            ):
                research_data += "\nSTAKEHOLDER STATUS:\n"
                stakeholders_info = []
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

            content = self._generate_response(context, research_data)

            # Create message
            message = DialogueMessage(role=self.role, content=content, timestamp=time.time())

        except Exception:
            logger.exception("Error in CPO Agent Run")
            return {}
        else:
            # Construct new history
            new_history = [*list(state.debate_history), message]
            return {"debate_history": new_history}
