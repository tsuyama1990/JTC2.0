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
        """Validates the graph to ensure no cyclic dependencies exist using Tarjan's strongly connected components algorithm."""
        adj_list: dict[str, list[str]] = {node: [] for node in self.nodes}
        adj_list["__end__"] = []

        for start, end in self.edges:
            if start not in self.nodes:
                msg = f"Edge references undefined start node: {start}"
                raise ValueError(msg)
            if end != "__end__" and end not in self.nodes:
                msg = f"Edge references undefined end node: {end}"
                raise ValueError(msg)

            if start not in adj_list:
                adj_list[start] = []
            if end not in adj_list:
                adj_list[end] = []
            adj_list[start].append(end)

        index = 0
        indices: dict[str, int] = {}
        lowlinks: dict[str, int] = {}
        on_stack: set[str] = set()
        stack: list[str] = []

        def strongconnect(v: str) -> None:
            nonlocal index
            indices[v] = index
            lowlinks[v] = index
            index += 1
            stack.append(v)
            on_stack.add(v)

            for w in adj_list.get(v, []):
                if v == w:
                    msg = f"Self-loop detected on node {v}."
                    raise ValueError(msg)

                if w not in indices:
                    strongconnect(w)
                    lowlinks[v] = min(lowlinks[v], lowlinks[w])
                elif w in on_stack:
                    lowlinks[v] = min(lowlinks[v], indices[w])

            if lowlinks[v] == indices[v]:
                component = []
                while True:
                    w = stack.pop()
                    on_stack.remove(w)
                    component.append(w)
                    if w == v:
                        break
                if len(component) > 1:
                    msg = "Cyclic dependency detected in graph structure."
                    raise ValueError(msg)

        for node in list(adj_list.keys()):
            if node not in indices:
                strongconnect(node)

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
