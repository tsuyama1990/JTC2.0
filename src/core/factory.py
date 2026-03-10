from pathlib import Path

from src.agents.builder import BuilderAgent
from src.agents.cpo import CPOAgent
from src.agents.governance import GovernanceAgent
from src.agents.ideator import IdeatorAgent
from src.agents.personas import FinanceAgent, NewEmployeeAgent, SalesAgent
from src.core.config import get_settings
from src.core.llm import get_llm
from src.domain_models.simulation import Role
from src.domain_models.state import GlobalState


class AgentFactory:
    """Factory for creating agents with dependencies injected."""

    @staticmethod
    def get_ideator_agent() -> IdeatorAgent:
        llm = get_llm()
        return IdeatorAgent(llm)

    @staticmethod
    def get_builder_agent() -> BuilderAgent:
        llm = get_llm()
        return BuilderAgent(llm)

    @staticmethod
    def get_governance_agent() -> GovernanceAgent:
        """Create a new Governance Agent."""
        return GovernanceAgent()

    @staticmethod
    def get_persona_agent(
        role: Role, state: GlobalState | None = None
    ) -> CPOAgent | NewEmployeeAgent | FinanceAgent | SalesAgent:
        """
        Get a persona agent instance.

        Args:
            role: The role to create.
            state: GlobalState, required for CPOAgent to get rag_index_path.
        """
        # CPO needs state context, so it's harder to cache globally without state key.
        # But other personas are stateless w.r.t construction.
        if role == Role.CPO:
            llm = get_llm()
            settings = get_settings()
            raw_path = state.rag_index_path if state else settings.rag_persist_dir
            resolved_path = Path(raw_path).resolve()

            import tempfile

            # Allow base dir to be current working directory or a specific temp dir.
            base_dir = Path.cwd().resolve()
            tmp_dir = Path(tempfile.gettempdir()).resolve()
            if not resolved_path.is_relative_to(base_dir) and not resolved_path.is_relative_to(tmp_dir):
                msg = f"Invalid RAG path: {resolved_path}. Must be relative to {base_dir}"
                raise ValueError(msg)

            return CPOAgent(llm, app_settings=settings, rag_path=str(resolved_path))

        return AgentFactory._create_persona_agent(role)

    @staticmethod
    def _create_persona_agent(role: Role) -> NewEmployeeAgent | FinanceAgent | SalesAgent:
        """
        Factory for stateless persona agents.
        """
        llm = get_llm()
        settings = get_settings()

        if role == Role.NEW_EMPLOYEE:
            return NewEmployeeAgent(llm, app_settings=settings)
        if role == Role.FINANCE:
            return FinanceAgent(llm, app_settings=settings)
        if role == Role.SALES:
            return SalesAgent(llm, app_settings=settings)

        msg = f"Unknown role: {role}"
        raise ValueError(msg)
