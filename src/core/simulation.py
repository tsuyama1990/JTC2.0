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
from functools import lru_cache
from typing import Any

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.agents.personas import FinanceAgent, NewEmployeeAgent, SalesAgent
from src.core.llm import get_llm
from src.domain_models.simulation import Role
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


# Use LRU cache to prevent memory leaks from unbounded @cache
@lru_cache(maxsize=10)
def _get_cached_agent(role: Role) -> Any:
    """
    Singleton-like access for agents to prevent recreation loops.
    """
    llm = get_llm()
    if role == Role.NEW_EMPLOYEE:
        return NewEmployeeAgent(llm)
    if role == Role.FINANCE:
        return FinanceAgent(llm)
    if role == Role.SALES:
        return SalesAgent(llm)
    raise ValueError(f"Unknown role: {role}")


def create_simulation_graph() -> CompiledStateGraph:  # type: ignore[type-arg]
    """Create the simulation sub-graph."""

    # We use the cached factory inside node functions

    def run_pitch(state: GlobalState) -> dict[str, object]:
        logger.info("Turn 1: New Employee Pitch")
        return _get_cached_agent(Role.NEW_EMPLOYEE).run(state)

    def run_finance(state: GlobalState) -> dict[str, object]:
        logger.info("Turn 2: Finance Critique")
        return _get_cached_agent(Role.FINANCE).run(state)

    def run_defense_1(state: GlobalState) -> dict[str, object]:
        logger.info("Turn 3: New Employee Defense")
        return _get_cached_agent(Role.NEW_EMPLOYEE).run(state)

    def run_sales(state: GlobalState) -> dict[str, object]:
        logger.info("Turn 4: Sales Critique")
        return _get_cached_agent(Role.SALES).run(state)

    def run_defense_2(state: GlobalState) -> dict[str, object]:
        logger.info("Turn 5: New Employee Final Defense")
        return _get_cached_agent(Role.NEW_EMPLOYEE).run(state)

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
