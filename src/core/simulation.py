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
from typing import cast

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

    # Lazy initialization: Create agents only when needed (inside the node functions)
    # However, LangGraph nodes are functions that receive state.
    # To avoid recreating agents on every invocation if this graph is compiled once,
    # we can use a closure or a factory.
    # But here, create_simulation_graph is called during app creation (or dynamically).
    # If dynamically (as per safe_simulation_run), then we want lightweight creation.
    #
    # Actually, the agents are stateful (caching), so recreating them might lose cache if not shared.
    # The requirement says "Lazy agent initialization or use dependency injection".
    #
    # Let's instantiate them inside the node functions using a cached factory or similar
    # if we want strictly lazy. But these are small objects if LLM is shared.
    # The expensive part is loading models (which get_llm does lazily/cached).
    #
    # Let's use a simple lazy pattern: Only init when the node runs.
    # But wait, nodes are defined below.
    # If we define `run_pitch` to init NewEmployeeAgent inside, it's lazy.

    def run_pitch(state: GlobalState) -> dict[str, object]:
        logger.info("Turn 1: New Employee Pitch")
        agent = NewEmployeeAgent(llm)
        return agent.run(state)

    def run_finance(state: GlobalState) -> dict[str, object]:
        logger.info("Turn 2: Finance Critique")
        agent = FinanceAgent(llm)
        return agent.run(state)

    def run_defense_1(state: GlobalState) -> dict[str, object]:
        logger.info("Turn 3: New Employee Defense")
        agent = NewEmployeeAgent(llm)
        return agent.run(state)

    def run_sales(state: GlobalState) -> dict[str, object]:
        logger.info("Turn 4: Sales Critique")
        agent = SalesAgent(llm)
        return agent.run(state)

    def run_defense_2(state: GlobalState) -> dict[str, object]:
        logger.info("Turn 5: New Employee Final Defense")
        agent = NewEmployeeAgent(llm)
        return agent.run(state)

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
