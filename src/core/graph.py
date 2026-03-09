import logging

from langgraph.graph import END
from langgraph.graph.state import CompiledStateGraph

from src.core.workflow_builder import WorkflowBuilder, node_registry
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


def _register_nodes(builder: WorkflowBuilder[GlobalState]) -> None:
    """Register all nodes into the workflow builder using the registry."""
    import src.core.nodes  # noqa: F401
    for name, func in node_registry.nodes.items():
        builder.add_node(name, func)


def _register_edges(builder: WorkflowBuilder[GlobalState]) -> None:
    """Register all edges mapping the workflow."""
    builder.set_entry_point("ideator")

    # Gate 1: Idea Verification
    builder.add_edge("ideator", "verification")
    builder.add_edge("verification", "persona")
    builder.add_edge("persona", "alternative_analysis")
    builder.add_edge("alternative_analysis", "vpc")

    # Gate 1.5: CPF Feedback (Interrupt after VPC)
    builder.add_edge("vpc", "transcript_ingestion")

    # Phase 3
    builder.add_edge("transcript_ingestion", "mental_model_journey")
    builder.add_edge("mental_model_journey", "sitemap_wireframe")

    # Gate 1.8: PSF Feedback (Interrupt after Sitemap)
    builder.add_edge("sitemap_wireframe", "virtual_customer")

    # Gate 2: Virtual Market Pivot Decision (Interrupt after Virtual Customer)
    builder.add_edge("virtual_customer", "simulation_round")

    builder.add_edge("simulation_round", "review_3h")

    builder.add_edge("review_3h", "spec_generation")
    builder.add_edge("spec_generation", "experiment_planning")

    # Gate 3: Final Output FB (Interrupt after Experiment Plan)
    builder.add_edge("experiment_planning", "governance")
    builder.add_edge("governance", END)


def _configure_interrupts(builder: WorkflowBuilder[GlobalState]) -> None:
    """Configure human-in-the-loop interruption points."""
    interrupts = ["ideator", "vpc", "sitemap_wireframe", "virtual_customer", "experiment_planning"]
    builder.set_interrupts(interrupts)


from typing import Any
def create_app(builder: WorkflowBuilder[GlobalState] | None = None) -> CompiledStateGraph[Any, Any]:
    """
    Create and compile the LangGraph application.
    This graph implements the "The JTC 2.0" architecture with documented HITL Gates.
    """
    if builder is None:
        builder = WorkflowBuilder[GlobalState](GlobalState)
        _register_nodes(builder)
        _register_edges(builder)
        _configure_interrupts(builder)

    return builder.build()
