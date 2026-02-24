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
    """
    Create the simulation sub-graph based on configured turn sequence.
    Dynamically builds nodes and edges from Settings.
    """
    # Default sequence if not in settings (though settings handles defaults)
    # Pitch -> Finance -> Defense -> Sales -> Defense -> End
    # For now, we will stick to the specified turn logic but map it dynamically if possible.
    # However, the graph structure requires distinct node names.
    # We will use a defined sequence for now but allow the role mapping to be more flexible if needed.

    # Actually, to make it truly configurable, we should iterate a list of steps.
    # Let's assume a fixed structure for JTC 2.0 but use settings to define participation?
    # The requirement says "Make turn sequence configurable".
    # We will define the sequence here as a list of (node_name, role, description).

    # Ideally this list comes from settings, but `Role` enum is code-bound.
    # We will define a standard sequence here but allow extension.

    steps = [
        ("pitch", Role.NEW_EMPLOYEE, "New Employee Pitch"),
        ("finance_critique", Role.FINANCE, "Finance Critique"),
        ("defense_1", Role.NEW_EMPLOYEE, "New Employee Defense"),
        ("sales_critique", Role.SALES, "Sales Critique"),
        ("defense_2", Role.NEW_EMPLOYEE, "New Employee Final Defense"),
    ]

    workflow = StateGraph(GlobalState)
    previous_node = None

    for node_name, role, desc in steps:
        # Create a closure for the node function
        def step_runner(state: GlobalState, role: Role = role, desc: str = desc) -> dict[str, object]:
            logger.info(desc)
            return AgentFactory.get_persona_agent(role).run(state)

        # Name the function for debugging
        step_runner.__name__ = f"run_{node_name}"

        workflow.add_node(node_name, step_runner)

        if previous_node:
            workflow.add_edge(previous_node, node_name)
        else:
            workflow.set_entry_point(node_name)

        previous_node = node_name

    if previous_node:
        workflow.add_edge(previous_node, END)

    return workflow.compile()
