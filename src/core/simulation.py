"""
Implements the turn-based simulation logic for the 'JTC 2.0' architecture.

This module defines the 'Battle' subgraph where agents debate.
The sequence is loaded from configuration to allow flexibility.
"""

import logging

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.core.config import get_settings
from src.core.factory import AgentFactory
from src.domain_models.simulation import Role
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


def create_simulation_graph() -> CompiledStateGraph:  # type: ignore[type-arg]
    """
    Create the simulation sub-graph based on configured turn sequence.
    Dynamically builds nodes and edges from Settings.
    """
    settings = get_settings()

    # Load sequence from settings.
    # Settings.simulation.turn_sequence is a list of dicts.
    # We validate the role strings against the Role enum.

    steps = settings.simulation.turn_sequence

    workflow = StateGraph(GlobalState)
    previous_node = None

    for step in steps:
        node_name = step["node_name"]
        role_str = step["role"]
        desc = step["description"]

        # Ensure role is a valid Role enum member
        try:
            role = Role(role_str)
        except ValueError:
            logger.exception(
                f"Invalid role '{role_str}' in simulation config. Skipping step {node_name}."
            )
            continue

        # Create a closure for the node function
        # We must bind defaults to capture the current iteration's values
        def step_runner(
            state: GlobalState, _role: Role = role, _desc: str = desc
        ) -> dict[str, object]:
            logger.info(_desc)
            # Add type ignore for Any return from run
            return AgentFactory.get_persona_agent(_role).run(state)  # type: ignore[no-any-return]

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
