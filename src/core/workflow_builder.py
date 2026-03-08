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
        """Validates the graph to ensure no cyclic dependencies exist using Kahn's Algorithm."""
        # Setup in-degrees and adjacency list
        in_degree: dict[str, int] = dict.fromkeys(self.nodes, 0)
        adj_list: dict[str, list[str]] = {node: [] for node in self.nodes}

        for start, end in self.edges:
            if end != "__end__":
                if end not in in_degree:
                    in_degree[end] = 0
                    adj_list[end] = []
                adj_list[start].append(end)
                in_degree[end] += 1

        # Find all nodes with 0 in-degree
        from collections import deque

        queue = deque([node for node in in_degree if in_degree[node] == 0])

        visited_count = 0
        while queue:
            current = queue.popleft()
            visited_count += 1

            for neighbor in adj_list.get(current, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # If we couldn't visit all nodes that have edges/definitions, there's a cycle
        if visited_count != len(in_degree):
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
