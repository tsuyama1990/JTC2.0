from langchain_openai import ChatOpenAI

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
from src.core.config import Settings
from src.domain_models.simulation import Role
from src.domain_models.state import GlobalState


class AgentFactory:
    """Factory for creating agents with dependencies injected."""

    def __init__(self, llm: ChatOpenAI, settings: Settings) -> None:
        self.llm = llm
        self.settings = settings

    def get_ideator_agent(self) -> IdeatorAgent:
        return IdeatorAgent(self.llm)

    def get_builder_agent(self) -> BuilderAgent:
        return BuilderAgent(self.llm)

    def get_governance_agent(self) -> GovernanceAgent:
        """Create a new Governance Agent."""
        return GovernanceAgent()

    def get_remastered_agent(self) -> RemasteredAgent:
        """Create a Remastered workflow agent."""
        return RemasteredAgent(self.llm)

    def get_output_generation_agent(self) -> OutputGenerationAgent:
        """Create an Output Generation workflow agent."""
        return OutputGenerationAgent(self.llm)

    def get_virtual_customer_agent(self) -> VirtualCustomerAgent:
        """Create a Virtual Customer Agent."""
        return VirtualCustomerAgent(self.llm)

    def get_hacker_agent(self) -> HackerAgent:
        """Create a Hacker Agent."""
        return HackerAgent(self.llm)

    def get_hipster_agent(self) -> HipsterAgent:
        """Create a Hipster Agent."""
        return HipsterAgent(self.llm)

    def get_hustler_agent(self) -> HustlerAgent:
        """Create a Hustler Agent."""
        return HustlerAgent(self.llm)

    def get_cpo_agent(self, state: GlobalState | None = None) -> CPOAgent:
        """Create a CPO Agent."""
        rag_path = state.rag_index_path if state else self.settings.rag.persist_dir
        return CPOAgent(self.llm, app_settings=self.settings, rag_path=rag_path)

    def get_new_employee_agent(self) -> NewEmployeeAgent:
        """Create a New Employee Agent."""
        return NewEmployeeAgent(self.llm, app_settings=self.settings)

    def get_finance_agent(self) -> FinanceAgent:
        """Create a Finance Agent."""
        return FinanceAgent(self.llm, app_settings=self.settings)

    def get_sales_agent(self) -> SalesAgent:
        """Create a Sales Agent."""
        return SalesAgent(self.llm, app_settings=self.settings)

    def get_persona_agent(
        self, role: Role, state: GlobalState | None = None
    ) -> CPOAgent | NewEmployeeAgent | FinanceAgent | SalesAgent:
        """
        Get a persona agent instance. Maps role to specific factory method.

        Args:
            role: The role to create.
            state: GlobalState, required for CPOAgent to get rag_index_path.
        """
        match role:
            case Role.CPO:
                return self.get_cpo_agent(state)
            case Role.NEW_EMPLOYEE:
                return self.get_new_employee_agent()
            case Role.FINANCE:
                return self.get_finance_agent()
            case Role.SALES:
                return self.get_sales_agent()
            case _:
                msg = f"Unknown role requested in AgentFactory: {role}"
                raise ValueError(msg)
