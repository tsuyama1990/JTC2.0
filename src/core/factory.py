from src.agents.builder import BuilderAgent
from src.agents.cpo import CPOAgent
from src.agents.governance import GovernanceAgent
from src.agents.ideator import IdeatorAgent
from src.agents.personas import FinanceAgent, NewEmployeeAgent, SalesAgent
from src.agents.remastered import (
    HackerAgent,
    HipsterAgent,
    HustlerAgent,
    OutputGenerationAgent,
    RemasteredAgent,
    VirtualCustomerAgent,
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
    def get_builder_agent() -> BuilderAgent:
        llm = get_llm()
        return BuilderAgent(llm)

    @staticmethod
    def get_governance_agent() -> GovernanceAgent:
        """Create a new Governance Agent."""
        return GovernanceAgent()

    @staticmethod
    def get_remastered_agent() -> RemasteredAgent:
        """Create a Remastered workflow agent."""
        llm = get_llm()
        return RemasteredAgent(llm)

    @staticmethod
    def get_output_generation_agent() -> OutputGenerationAgent:
        """Create an Output Generation workflow agent."""
        llm = get_llm()
        return OutputGenerationAgent(llm)

    @staticmethod
    def get_virtual_customer_agent() -> VirtualCustomerAgent:
        """Create a Virtual Customer Agent."""
        llm = get_llm()
        return VirtualCustomerAgent(llm)

    @staticmethod
    def get_hacker_agent() -> HackerAgent:
        """Create a Hacker Agent."""
        llm = get_llm()
        return HackerAgent(llm)

    @staticmethod
    def get_hipster_agent() -> HipsterAgent:
        """Create a Hipster Agent."""
        llm = get_llm()
        return HipsterAgent(llm)

    @staticmethod
    def get_hustler_agent() -> HustlerAgent:
        """Create a Hustler Agent."""
        llm = get_llm()
        return HustlerAgent(llm)

    @staticmethod
    def get_cpo_agent(state: GlobalState | None = None) -> CPOAgent:
        """Create a CPO Agent."""
        llm = get_llm()
        settings = get_settings()
        rag_path = state.rag_index_path if state else settings.rag_persist_dir
        return CPOAgent(llm, app_settings=settings, rag_path=rag_path)

    @staticmethod
    def get_new_employee_agent() -> NewEmployeeAgent:
        """Create a New Employee Agent."""
        return NewEmployeeAgent(get_llm(), app_settings=get_settings())

    @staticmethod
    def get_finance_agent() -> FinanceAgent:
        """Create a Finance Agent."""
        return FinanceAgent(get_llm(), app_settings=get_settings())

    @staticmethod
    def get_sales_agent() -> SalesAgent:
        """Create a Sales Agent."""
        return SalesAgent(get_llm(), app_settings=get_settings())

    @staticmethod
    def get_persona_agent(
        role: Role, state: GlobalState | None = None
    ) -> CPOAgent | NewEmployeeAgent | FinanceAgent | SalesAgent:
        """
        Get a persona agent instance. Maps role to specific factory method.

        Args:
            role: The role to create.
            state: GlobalState, required for CPOAgent to get rag_index_path.
        """
        match role:
            case Role.CPO:
                return AgentFactory.get_cpo_agent(state)
            case Role.NEW_EMPLOYEE:
                return AgentFactory.get_new_employee_agent()
            case Role.FINANCE:
                return AgentFactory.get_finance_agent()
            case Role.SALES:
                return AgentFactory.get_sales_agent()
            case _:
                msg = f"Unknown role requested in AgentFactory: {role}"
                raise ValueError(msg)
