from typing import Any

from src.agents.builder import BuilderAgent
from src.agents.cpo import CPOAgent
from src.agents.governance import GovernanceAgent
from src.agents.ideator import IdeatorAgent
from src.agents.personas import (
    AlternativeAnalysisAgent,
    FinanceAgent,
    NewEmployeeAgent,
    PersonaGeneratorAgent,
    SalesAgent,
    ValuePropositionAgent,
)
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
    def get_persona_generator_agent() -> PersonaGeneratorAgent:
        llm = get_llm()
        return PersonaGeneratorAgent(llm)

    @staticmethod
    def get_alternative_analysis_agent() -> AlternativeAnalysisAgent:
        llm = get_llm()
        return AlternativeAnalysisAgent(llm)

    @staticmethod
    def get_vpc_agent() -> ValuePropositionAgent:
        llm = get_llm()
        return ValuePropositionAgent(llm)

    @staticmethod
    def get_builder_agent() -> BuilderAgent:
        llm = get_llm()
        return BuilderAgent(llm)

    @staticmethod
    def get_governance_agent() -> GovernanceAgent:
        """Create a new Governance Agent."""
        return GovernanceAgent()

    @staticmethod
    def get_persona_agent(role: Role, state: GlobalState) -> Any:
        """
        Get a persona agent instance.

        Args:
            role: The role to create.
            state: GlobalState, required for context dependencies like RAG paths.
        """
        llm = get_llm()
        settings = get_settings()

        if role == Role.CPO:
            rag_path = state.rag_index_path if state else settings.rag_persist_dir
            return CPOAgent(llm, app_settings=settings, rag_path=rag_path)

        # Assuming all persona agents in the future could need state
        if role == Role.NEW_EMPLOYEE:
            return NewEmployeeAgent(llm, app_settings=settings)
        if role == Role.FINANCE:
            return FinanceAgent(llm, app_settings=settings)
        if role == Role.SALES:
            return SalesAgent(llm, app_settings=settings)

        msg = f"Unknown role: {role}"
        raise ValueError(msg)
