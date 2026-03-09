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
        node_name = step.get("node_name")
        role_str = step.get("role")
        desc = step.get("description", "Simulation Step")

        if not node_name or not isinstance(node_name, str):
            msg = "Simulation step must have a valid string 'node_name'."
            raise ValueError(msg)
        if not role_str or not isinstance(role_str, str):
            msg = "Simulation step must have a valid string 'role'."
            raise ValueError(msg)

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

        from functools import partial

        # Create a closure for the node function
        def _execute_step(
            state: GlobalState, bound_role: Role, bound_desc: str
        ) -> dict[str, object]:
            from src.core.config import get_settings
            from src.core.llm import LLMFactory

            logger.info(bound_desc)
            factory = AgentFactory(llm=LLMFactory().get_llm(), settings=get_settings())
            res = factory.get_persona_agent(bound_role).run(state)
            return res if isinstance(res, dict) else {}

        # We must bind defaults securely using partial to prevent late binding loop closures
        bound_runner = partial(_execute_step, bound_role=role, bound_desc=desc)

        # For LangGraph tracking, we can wrap the partial to give it a proper name
        def named_runner(state: GlobalState, _runner: Any = bound_runner) -> dict[str, object]:
            res = _runner(state)
            return res if isinstance(res, dict) else {}

        named_runner.__name__ = f"run_{node_name}"

        workflow.add_node(node_name, named_runner)

        if previous_node:
            workflow.add_edge(previous_node, node_name)
        else:
            workflow.set_entry_point(node_name)

        previous_node = node_name

    if previous_node:
        workflow.add_edge(previous_node, END)

    return workflow.compile()
