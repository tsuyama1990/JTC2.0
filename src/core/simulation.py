"""
Implements the turn-based simulation logic for the 'JTC 2.0' architecture.

This module defines the 'Battle' subgraph where agents debate.
The sequence is loaded from configuration to allow flexibility.
"""

import logging
from typing import Any

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.core.config import get_settings
from src.core.factory import AgentFactory
from src.domain_models.simulation import Role
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


def create_simulation_graph() -> CompiledStateGraph[Any, Any]:
    """
    Create the simulation sub-graph based on configured turn sequence.
    Dynamically builds nodes and edges from Settings.
    """
    settings = get_settings()

    # Load sequence from settings.
    # Settings.simulation.turn_sequence is a list of dicts.
    # We validate the role strings against the Role enum.

    steps = settings.simulation.turn_sequence

    MAX_SIMULATION_STEPS = 50
    if len(steps) > MAX_SIMULATION_STEPS:
        msg = f"Simulation step count exceeds maximum allowed limit ({MAX_SIMULATION_STEPS})."
        raise ValueError(msg)

    workflow = StateGraph(GlobalState)
    previous_node = None

    import re

    for step in steps:
        node_name = step["node_name"]
        role_str = step["role"]
        desc = step["description"]

        # Strict validation of node_name to prevent code injection via name manipulation
        if not re.match(r"^[a-zA-Z0-9_-]+$", node_name):
            msg = f"Invalid node_name '{node_name}' in simulation config. Must be alphanumeric."
            raise ValueError(msg)

        # Ensure role is a valid Role enum member (acts as a strict whitelist)
        try:
            role = Role(role_str)
        except ValueError as err:
            msg = f"Invalid role '{role_str}' in simulation config. Must be one of {list(Role)}."
            raise ValueError(msg) from err

        # Create a closure for the node function
        # We must bind defaults to capture the current iteration's values
        def step_runner(
            state: GlobalState, _role: Role = role, _desc: str = desc
        ) -> dict[str, object]:
            from src.core.config import get_settings
            from src.core.llm import LLMFactory

            logger.info(_desc)
            factory = AgentFactory(llm=LLMFactory().get_llm(), settings=get_settings())
            return factory.get_persona_agent(_role).run(state)

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
