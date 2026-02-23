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

from src.agents.personas import FinanceAgent, NewEmployeeAgent, SalesAgent
from src.core.llm import get_llm
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


def create_simulation_graph() -> CompiledStateGraph:  # type: ignore[type-arg]
    """Create the simulation sub-graph."""
    # Ensure dependencies are available
    llm = get_llm()

    # Initialize agents
    new_employee = NewEmployeeAgent(llm)
    finance = FinanceAgent(llm)
    sales = SalesAgent(llm)

    workflow = StateGraph(GlobalState)

    # Add Nodes
    # We use distinct node names to define the sequence,
    # even though they reuse the same agent instances.

    # Wrap agents with logging for debug visibility
    def run_pitch(state: GlobalState) -> dict[str, object]:
        logger.info("Turn 1: New Employee Pitch")
        return new_employee.run(state)

    def run_finance(state: GlobalState) -> dict[str, object]:
        logger.info("Turn 2: Finance Critique")
        return finance.run(state)

    def run_defense_1(state: GlobalState) -> dict[str, object]:
        logger.info("Turn 3: New Employee Defense")
        return new_employee.run(state)

    def run_sales(state: GlobalState) -> dict[str, object]:
        logger.info("Turn 4: Sales Critique")
        return sales.run(state)

    def run_defense_2(state: GlobalState) -> dict[str, object]:
        logger.info("Turn 5: New Employee Final Defense")
        return new_employee.run(state)

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
