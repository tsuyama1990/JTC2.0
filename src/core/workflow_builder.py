import logging
from collections.abc import Callable
from typing import Any, Generic, TypeVar

from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)

T = TypeVar("T")

class WorkflowRegistry(Generic[T]):
    """Registry for declarative workflow nodes."""
    def __init__(self) -> None:
        self.nodes: dict[str, Callable[[T], dict[str, Any]]] = {}

    def register(self, name: str) -> Callable[[Callable[[T], dict[str, Any]]], Callable[[T], dict[str, Any]]]:
        def decorator(func: Callable[[T], dict[str, Any]]) -> Callable[[T], dict[str, Any]]:
            self.nodes[name] = func
            return func
        return decorator

node_registry: WorkflowRegistry[GlobalState] = WorkflowRegistry()

class WorkflowBuilder(Generic[T]):
    """Builds the StateGraph workflow, decoupling structure from implementation."""

    def __init__(self, state_schema: type[Any]) -> None:
        self.workflow = StateGraph(state_schema)
        self.nodes: dict[str, Callable[[Any], dict[str, Any]]] = {}
        self.edges: list[tuple[str, str]] = []
        self.entry_point: str | None = None
        self.interrupts: list[str] = []

    def add_node(self, name: str, action: Callable[[Any], dict[str, Any]]) -> "WorkflowBuilder[T]":
        """Add a node to the workflow."""
        self.nodes[name] = action
        return self

    def add_edge(self, start_key: str, end_key: str) -> "WorkflowBuilder[T]":
        """Add a directed edge between nodes."""
        self.edges.append((start_key, end_key))
        return self

    def set_entry_point(self, key: str) -> "WorkflowBuilder[T]":
        """Set the entry point of the graph."""
        self.entry_point = key
        return self

    def set_interrupts(self, interrupts: list[str]) -> "WorkflowBuilder[T]":
        """Set nodes to interrupt after."""
        self.interrupts = interrupts
        return self

    def _validate_no_cycles(self) -> None:
        """Validates the graph to ensure no cyclic dependencies exist using DFS back-edge detection."""
        adj_list: dict[str, list[str]] = {node: [] for node in self.nodes}
        adj_list["__end__"] = []

        for start, end in self.edges:
            if start not in self.nodes:
                msg = f"Edge references undefined start node: {start}"
                raise ValueError(msg)
            if end != "__end__" and end not in self.nodes:
                msg = f"Edge references undefined end node: {end}"
                raise ValueError(msg)

            if start == end:
                msg = f"Self-loop detected on node {start}."
                raise ValueError(msg)

            if start not in adj_list:
                adj_list[start] = []
            if end not in adj_list:
                adj_list[end] = []

            if end in adj_list[start]:
                msg = f"Parallel edges detected from {start} to {end}."
                raise ValueError(msg)

            adj_list[start].append(end)

        visited = set()
        path = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            path.add(node)

            for neighbor in adj_list.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in path:
                    return True

            path.remove(node)
            return False

        for node in adj_list:
            if node not in visited and dfs(node):
                msg = "Cyclic dependency detected in graph structure."
                raise ValueError(msg)

    def build(self) -> CompiledStateGraph[Any, Any]:
        """Constructs and compiles the graph with validations."""
        # Cycle detection
        self._validate_no_cycles()

        for name, action in self.nodes.items():
            self.workflow.add_node(name, action)  # type: ignore[call-overload]

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
