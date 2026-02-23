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

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.core.factory import AgentFactory
from src.domain_models.simulation import Role
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


def create_simulation_graph() -> CompiledStateGraph:  # type: ignore[type-arg]
    """Create the simulation sub-graph."""

    # We use the factory which handles caching

    def run_pitch(state: GlobalState) -> dict[str, object]:
        logger.info("Turn 1: New Employee Pitch")
        return AgentFactory.get_persona_agent(Role.NEW_EMPLOYEE).run(state)

    def run_finance(state: GlobalState) -> dict[str, object]:
        logger.info("Turn 2: Finance Critique")
        return AgentFactory.get_persona_agent(Role.FINANCE).run(state)

    def run_defense_1(state: GlobalState) -> dict[str, object]:
        logger.info("Turn 3: New Employee Defense")
        return AgentFactory.get_persona_agent(Role.NEW_EMPLOYEE).run(state)

    def run_sales(state: GlobalState) -> dict[str, object]:
        logger.info("Turn 4: Sales Critique")
        return AgentFactory.get_persona_agent(Role.SALES).run(state)

    def run_defense_2(state: GlobalState) -> dict[str, object]:
        logger.info("Turn 5: New Employee Final Defense")
        return AgentFactory.get_persona_agent(Role.NEW_EMPLOYEE).run(state)

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
