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


from collections.abc import Callable
from typing import Any

class AgentFactory:
    """Factory for creating agents using a dynamic registry to satisfy the Open/Closed Principle."""

    def __init__(self, llm: ChatOpenAI, settings: Settings) -> None:
        self.llm = llm
        self.settings = settings
        self._registry: dict[str, Callable[..., Any]] = {}
        self._register_defaults()

    def register(self, name: str, creator: Callable[..., Any]) -> None:
        """Register a new agent creator function."""
        self._registry[name] = creator

    def get(self, name: str, **kwargs: Any) -> Any:
        """Instantiate an agent by name."""
        if name not in self._registry:
            msg = f"Unknown agent requested in AgentFactory: {name}"
            raise ValueError(msg)
        return self._registry[name](**kwargs)

    def _register_defaults(self) -> None:
        """Register the default agent set."""
        from src.core.services.file_service import FileService, ThreadedFileWriter

        self.register("ideator", lambda: IdeatorAgent(self.llm))
        self.register("builder", lambda: BuilderAgent(self.llm))

        def _create_governance() -> GovernanceAgent:
            # Requires explicit IFileWriter and Settings per our previous refactor
            return GovernanceAgent(file_service=FileService(settings=self.settings, writer=ThreadedFileWriter()))
        self.register("governance", _create_governance)

        self.register("remastered", lambda: RemasteredAgent(self.llm))
        self.register("output_generation", lambda: OutputGenerationAgent(self.llm))
        self.register("virtual_customer", lambda: VirtualCustomerAgent(self.llm))
        self.register("hacker", lambda: HackerAgent(self.llm))
        self.register("hipster", lambda: HipsterAgent(self.llm))
        self.register("hustler", lambda: HustlerAgent(self.llm))

        def _create_cpo(state: GlobalState | None = None) -> CPOAgent:
            rag_path = state.rag_index_path if state else self.settings.rag.persist_dir
            return CPOAgent(self.llm, app_settings=self.settings, rag_path=rag_path)

        self.register("cpo", _create_cpo)
        self.register("new_employee", lambda: NewEmployeeAgent(self.llm, app_settings=self.settings))
        self.register("finance", lambda: FinanceAgent(self.llm, app_settings=self.settings))
        self.register("sales", lambda: SalesAgent(self.llm, app_settings=self.settings))

    # Backward compatibility wrappers wrapping the dynamic registry
    def get_ideator_agent(self) -> IdeatorAgent:
        return self.get("ideator")

    def get_builder_agent(self) -> BuilderAgent:
        return self.get("builder")

    def get_governance_agent(self) -> GovernanceAgent:
        return self.get("governance")

    def get_remastered_agent(self) -> RemasteredAgent:
        return self.get("remastered")

    def get_output_generation_agent(self) -> OutputGenerationAgent:
        return self.get("output_generation")

    def get_virtual_customer_agent(self) -> VirtualCustomerAgent:
        return self.get("virtual_customer")

    def get_hacker_agent(self) -> HackerAgent:
        return self.get("hacker")

    def get_hipster_agent(self) -> HipsterAgent:
        return self.get("hipster")

    def get_hustler_agent(self) -> HustlerAgent:
        return self.get("hustler")

    def get_cpo_agent(self, state: GlobalState | None = None) -> CPOAgent:
        return self.get("cpo", state=state)

    def get_new_employee_agent(self) -> NewEmployeeAgent:
        return self.get("new_employee")

    def get_finance_agent(self) -> FinanceAgent:
        return self.get("finance")

    def get_sales_agent(self) -> SalesAgent:
        return self.get("sales")

    def get_persona_agent(
        self, role: Role, state: GlobalState | None = None
    ) -> CPOAgent | NewEmployeeAgent | FinanceAgent | SalesAgent:
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
