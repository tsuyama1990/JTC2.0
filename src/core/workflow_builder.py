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

    def _validate_no_cycles(self) -> None:
        """Validates the graph to ensure no cyclic dependencies exist using Depth-First Search (DFS)."""
        adj_list: dict[str, list[str]] = {node: [] for node in self.nodes}
        adj_list["__end__"] = []

        for start, end in self.edges:
            if start not in adj_list:
                adj_list[start] = []
            if end not in adj_list:
                adj_list[end] = []
            adj_list[start].append(end)

        visited: set[str] = set()
        rec_stack: set[str] = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in adj_list.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in list(adj_list.keys()):
            if node not in visited and dfs(node):
                msg = "Cyclic dependency detected in graph structure."
                raise ValueError(msg)

    def build(self) -> CompiledStateGraph[Any, Any]:
        """Constructs and compiles the graph with validations."""
        # Cycle detection
        self._validate_no_cycles()

        for name, action in self.nodes.items():
            self.workflow.add_node(name, action)

        if self.entry_point:
            self.workflow.set_entry_point(self.entry_point)

        for start, end in self.edges:
            if start not in self.nodes:
                msg = f"Edge references invalid start node: {start}"
                raise ValueError(msg)
            if end != "__end__" and end not in self.nodes:
                msg = f"Edge references invalid end node: {end}"
                raise ValueError(msg)

            self.workflow.add_edge(start, end)

        # Validate interrupt sequence
        valid_nodes = set(self.nodes.keys())
        for node in self.interrupts:
            if node not in valid_nodes:
                msg = f"Invalid interrupt node configured: {node}"
                raise ValueError(msg)

        # Compile with Interrupts for documented HITL Gates
        return self.workflow.compile(interrupt_after=self.interrupts)
