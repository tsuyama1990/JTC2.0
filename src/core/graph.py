import logging
from typing import Any

from langgraph.graph import END
from langgraph.graph.state import CompiledStateGraph

from src.core.config import Settings
from src.core.factory import AgentFactory
from src.core.workflow_builder import WorkflowBuilder, WorkflowRegistry
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


class GraphBuilderService:
    """Builds the execution graph using the provided registry."""

    def __init__(
        self,
        registry: WorkflowRegistry[GlobalState],
        settings: Settings,
        agent_factory: AgentFactory | None = None,
    ) -> None:
        self.registry = registry
        self.settings = settings
        self.agent_factory = agent_factory

    def _register_nodes(
        self, builder: WorkflowBuilder[GlobalState]
    ) -> WorkflowBuilder[GlobalState]:
        """Register all nodes into the workflow builder using the registry."""
        current_builder = builder
        for name, func in self.registry.nodes.items():
            current_builder = current_builder.add_node(name, func)
        return current_builder

    def _register_edges(
        self, builder: WorkflowBuilder[GlobalState]
    ) -> WorkflowBuilder[GlobalState]:
        """Register all edges mapping the workflow."""
        current_builder = builder.set_entry_point("ideator")

        # Gate 1: Idea Verification
        current_builder = current_builder.add_edge("ideator", "verification")
        current_builder = current_builder.add_edge("verification", "persona")
        current_builder = current_builder.add_edge("persona", "alternative_analysis")
        current_builder = current_builder.add_edge("alternative_analysis", "vpc")

        # Gate 1.5: CPF Feedback (Interrupt after VPC)
        current_builder = current_builder.add_edge("vpc", "transcript_ingestion")

        # Phase 3
        current_builder = current_builder.add_edge("transcript_ingestion", "mental_model_journey")
        current_builder = current_builder.add_edge("mental_model_journey", "sitemap_wireframe")

        # Gate 1.8: PSF Feedback (Interrupt after Sitemap)
        current_builder = current_builder.add_edge("sitemap_wireframe", "virtual_customer")

        # Gate 2: Virtual Market Pivot Decision (Interrupt after Virtual Customer)
        current_builder = current_builder.add_edge("virtual_customer", "simulation_round")

        current_builder = current_builder.add_edge("simulation_round", "review_3h")

        current_builder = current_builder.add_edge("review_3h", "spec_generation")
        current_builder = current_builder.add_edge("spec_generation", "experiment_planning")

        # Gate 3: Final Output FB (Interrupt after Experiment Plan)
        current_builder = current_builder.add_edge("experiment_planning", "governance")
        return current_builder.add_edge("governance", END)

    def _configure_interrupts(
        self, builder: WorkflowBuilder[GlobalState]
    ) -> WorkflowBuilder[GlobalState]:
        """Configure human-in-the-loop interruption points."""
        interrupts = [
            "ideator",
            "vpc",
            "sitemap_wireframe",
            "virtual_customer",
            "experiment_planning",
        ]
        return builder.set_interrupts(interrupts)

    def build_graph(
        self, builder: WorkflowBuilder[GlobalState] | None = None
    ) -> CompiledStateGraph[Any, Any]:
        current_builder = (
            builder if builder is not None else WorkflowBuilder[GlobalState](GlobalState)
        )
        current_builder = self._register_nodes(current_builder)
        current_builder = self._register_edges(current_builder)
        current_builder = self._configure_interrupts(current_builder)
        return current_builder.build()


def create_app(
    registry: WorkflowRegistry[GlobalState],
    settings: Settings,
    agent_factory: AgentFactory | None = None,
    builder: WorkflowBuilder[GlobalState] | None = None,
) -> CompiledStateGraph[Any, Any]:
    """
    Create and compile the LangGraph application.
    This graph implements the "The JTC 2.0" architecture with documented HITL Gates.
    """
    try:
        service = GraphBuilderService(registry, settings, agent_factory)
        return service.build_graph(builder)
    except Exception as e:
        msg = f"Failed to build application graph: {e}"
        logger.exception(msg)
        err_msg = f"Workflow initialization failed: {e}"
        raise RuntimeError(err_msg) from e
