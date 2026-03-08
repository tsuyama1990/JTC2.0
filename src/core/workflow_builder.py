import logging
from typing import Any

from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


class WorkflowBuilder:
    """Builds the StateGraph workflow, decoupling structure from implementation."""

    def __init__(self) -> None:
        self.workflow = StateGraph(GlobalState)
        self.nodes: dict[str, Any] = {}
        self.edges: list[tuple[str, str]] = []
        self.entry_point: str | None = None
        self.interrupts: list[str] = []

    def add_node(self, name: str, action: Any) -> "WorkflowBuilder":
        """Add a node to the workflow."""
        self.nodes[name] = action
        return self

    def add_edge(self, start_key: str, end_key: str) -> "WorkflowBuilder":
        """Add a directed edge between nodes."""
        self.edges.append((start_key, end_key))
        return self

    def set_entry_point(self, key: str) -> "WorkflowBuilder":
        """Set the entry point of the graph."""
        self.entry_point = key
        return self

    def set_interrupts(self, interrupts: list[str]) -> "WorkflowBuilder":
        """Set nodes to interrupt after."""
        self.interrupts = interrupts
        return self

    def build(self) -> CompiledStateGraph[Any, Any]:
        """Constructs and compiles the graph."""
        for name, action in self.nodes.items():
            self.workflow.add_node(name, action)

        if self.entry_point:
            self.workflow.set_entry_point(self.entry_point)

        for start, end in self.edges:
            self.workflow.add_edge(start, end)

        # Validate interrupt sequence
        valid_nodes = set(self.nodes.keys())
        for node in self.interrupts:
            if node not in valid_nodes:
                msg = f"Invalid interrupt node configured: {node}"
                raise ValueError(msg)

        # Compile with Interrupts for documented HITL Gates
        return self.workflow.compile(interrupt_after=self.interrupts)
