"""
Implements the turn-based simulation logic for the 'JTC 2.0' architecture.

This module defines the 'Battle' subgraph where agents debate.
The sequence is loaded from configuration to allow flexibility.
"""

import functools
import logging
import threading
from collections.abc import Iterator
from typing import Any

from langgraph.graph import END, StateGraph

from src.core.config import get_settings
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.simulation import Role
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


def create_simulation_graph(agent_factory: Any = None) -> Any:
    """
    Create the simulation sub-graph based on configured turn sequence.
    Dynamically builds nodes and edges from Settings.
    """
    if agent_factory is None:
        from src.core.factory import AgentFactory

        agent_factory = AgentFactory()
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
        except ValueError as err:
            logger.exception(f"Critical configuration error: Invalid role '{role_str}'")
            msg = f"Invalid role '{role_str}' in simulation config step {node_name}."
            raise ValueError(msg) from err

        # Create a runner function avoiding late binding closure issues
        def _step_runner(state: GlobalState, bound_role: Role, bound_desc: str) -> dict[str, Any]:
            logger.info(bound_desc)
            return agent_factory.get_persona_agent(bound_role, state).run(state)  # type: ignore[no-any-return]

        # Bind the specific arguments for this iteration
        bound_runner = functools.partial(_step_runner, bound_role=role, bound_desc=desc)
        bound_runner.__name__ = f"run_{node_name}"  # type: ignore[attr-defined]

        workflow.add_node(node_name, bound_runner)

        if previous_node:
            workflow.add_edge(previous_node, node_name)
        else:
            workflow.set_entry_point(node_name)

        previous_node = node_name

    if previous_node:
        workflow.add_edge(previous_node, END)

    return workflow.compile()


class SimulationManager:
    """Encapsulates thread management for the simulation UI."""

    def __init__(self, initial_state: GlobalState, renderer_factory: Any) -> None:
        self.initial_state = initial_state
        self.shared_state = {"current": initial_state}
        self.renderer_factory = renderer_factory
        self.app = create_simulation_graph()
        self._thread: threading.Thread | None = None

    def _background_task(self) -> None:
        try:
            for state_update in self.app.stream(self.initial_state, stream_mode="values"):
                if isinstance(state_update, dict):
                    try:
                        self.shared_state["current"] = GlobalState(**state_update)
                    except Exception:
                        logger.exception("Failed to convert state update to GlobalState")
                elif isinstance(state_update, GlobalState):
                    self.shared_state["current"] = state_update
                else:
                    logger.warning(f"Unknown state update type: {type(state_update)}")
        except Exception:
            logger.exception("Simulation thread failed")

    def run(self) -> None:
        """Run the simulation graph in the background and start the renderer."""
        import threading

        self._thread = threading.Thread(target=self._background_task, daemon=True)
        self._thread.start()

        try:
            renderer = self.renderer_factory(lambda: self.shared_state["current"])
            renderer.start()
        finally:
            if self._thread and self._thread.is_alive():
                # Note: Python threads don't have a direct 'kill' mechanism.
                # They will shut down when daemon=True, but we join for clarity.
                self._thread.join(timeout=1.0)


class SimulationService:
    """Encapsulates LangGraph execution and state persistence, hiding 'app.stream' details from the CLI."""

    def __init__(self) -> None:
        from src.core.graph import create_app

        self.app = create_app()

    def run_ideation_to_gate(self, topic: str) -> tuple[Iterator["LeanCanvas"], GlobalState]:
        from collections.abc import Iterator

        from src.domain_models.lean_canvas import LeanCanvas
        from src.domain_models.state import Phase

        initial_state = {"topic": topic, "phase": Phase.IDEATION}

        final_state_data = None
        for output in self.app.stream(
            initial_state, {"recursion_limit": 5, "configurable": {"thread_id": "1"}}
        ):
            node_name = next(iter(output.keys()))
            final_state_data = output[node_name]

        if final_state_data is None:
            return iter([]), GlobalState(topic=topic)

        state_obj = (
            GlobalState(**final_state_data)
            if isinstance(final_state_data, dict)
            else final_state_data
        )
        generated_ideas_raw = getattr(state_obj, "generated_ideas", [])

        iterator = (
            iter(generated_ideas_raw) if hasattr(generated_ideas_raw, "__iter__") else iter([])
        )

        def _yield_items() -> Iterator[LeanCanvas]:
            for item in iterator:
                if isinstance(item, LeanCanvas):
                    yield item
                elif isinstance(item, dict):
                    try:
                        yield LeanCanvas(**item)
                    except Exception:
                        logger.exception("Failed to parse idea")
                        continue
                else:
                    logger.warning(f"Unknown item type in generated ideas: {type(item)}")

        return _yield_items(), state_obj

    def resume_after_gate(self, selected_idea: "LeanCanvas") -> None:
        from langgraph.types import Command

        self.app.invoke(
            Command(resume={"selected_idea": selected_idea.model_dump()}),
            {"configurable": {"thread_id": "1"}},
        )
