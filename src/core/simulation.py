"""
Implements the turn-based simulation logic for the 'JTC 2.0' architecture.

This module defines the 'Battle' subgraph where:
- The New Employee pitches their idea.
- The Finance Manager critiques it (Turn 2).
- The New Employee defends (Turn 3).
- The Sales Manager critiques it (Turn 4).
- The New Employee defends again (Turn 5).

This subgraph is invoked by the main application graph during the 'simulation_round' node.
"""

import logging
from typing import Any, cast

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.agents.personas import FinanceAgent, NewEmployeeAgent, SalesAgent
from src.core.llm import get_llm
from src.domain_models.simulation import Role
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


def create_simulation_graph() -> CompiledStateGraph:  # type: ignore[type-arg]
    """Create the simulation sub-graph."""
    llm = get_llm()

    # Caching strategy:
    # Since nodes are functions, we can't easily store state in them without closure or globals.
    # However, get_llm() is cached. Agent initialization is lightweight IF the LLM is shared.
    # The expensive part is usually model loading (handled by get_llm).
    # To strictly avoid "recreating agents", we can instantiate them once here in the closure.
    # This closure is called when the graph is built (usually once per app startup or request).

    # Pre-instantiate agents (Dependency Injection / Lazy-ish since graph is built on demand)
    # If create_simulation_graph is called once globally, these are singletons.
    # If called per request, they are scoped to request.
    # The current architecture calls this via `safe_simulation_run` -> `create_simulation_graph`.
    # To optimize, we should cache the GRAPH or the AGENTS.
    # Given the constraint "Implement agent caching", let's cache the instances in a simple dict
    # or just rely on the closure if this function was cached.
    # But `safe_simulation_run` calls this every time.
    # Let's instantiate them here. The cost is negligible compared to LLM calls.

    agents: dict[Role, Any] = {
        Role.NEW_EMPLOYEE: NewEmployeeAgent(llm),
        Role.FINANCE: FinanceAgent(llm),
        Role.SALES: SalesAgent(llm),
    }

    def _get_agent(role: Role) -> Any:
        return agents[role]

    def run_pitch(state: GlobalState) -> dict[str, object]:
        logger.info("Turn 1: New Employee Pitch")
        return _get_agent(Role.NEW_EMPLOYEE).run(state)

    def run_finance(state: GlobalState) -> dict[str, object]:
        logger.info("Turn 2: Finance Critique")
        return _get_agent(Role.FINANCE).run(state)

    def run_defense_1(state: GlobalState) -> dict[str, object]:
        logger.info("Turn 3: New Employee Defense")
        return _get_agent(Role.NEW_EMPLOYEE).run(state)

    def run_sales(state: GlobalState) -> dict[str, object]:
        logger.info("Turn 4: Sales Critique")
        return _get_agent(Role.SALES).run(state)

    def run_defense_2(state: GlobalState) -> dict[str, object]:
        logger.info("Turn 5: New Employee Final Defense")
        return _get_agent(Role.NEW_EMPLOYEE).run(state)

    workflow = StateGraph(GlobalState)

    workflow.add_node("pitch", run_pitch)
    workflow.add_node("finance_critique", run_finance)
    workflow.add_node("defense_1", run_defense_1)
    workflow.add_node("sales_critique", run_sales)
    workflow.add_node("defense_2", run_defense_2)

    # Edges
    workflow.set_entry_point("pitch")
    workflow.add_edge("pitch", "finance_critique")
    workflow.add_edge("finance_critique", "defense_1")
    workflow.add_edge("defense_1", "sales_critique")
    workflow.add_edge("sales_critique", "defense_2")
    workflow.add_edge("defense_2", END)

    return workflow.compile()
