import logging
from typing import Any

from langgraph.graph import END
from langgraph.graph.state import CompiledStateGraph

from src.core.nodes import (
    alternative_analysis_node,
    experiment_planning_node,
    governance_node,
    mental_model_journey_node,
    persona_node,
    review_3h_node,
    safe_ideator_run,
    safe_simulation_run,
    sitemap_wireframe_node,
    spec_generation_node,
    transcript_ingestion_node,
    verification_node,
    virtual_customer_node,
    vpc_node,
)
from src.core.workflow_builder import WorkflowBuilder

logger = logging.getLogger(__name__)


def _register_nodes(builder: WorkflowBuilder) -> None:
    """Register all nodes into the workflow builder."""
    builder.add_node("ideator", safe_ideator_run)
    builder.add_node("verification", verification_node)

    # Phase 2
    builder.add_node("persona", persona_node)
    builder.add_node("alternative_analysis", alternative_analysis_node)
    builder.add_node("vpc", vpc_node)
    builder.add_node("transcript_ingestion", transcript_ingestion_node)

    # Phase 3
    builder.add_node("mental_model_journey", mental_model_journey_node)
    builder.add_node("sitemap_wireframe", sitemap_wireframe_node)

    # Phase 4
    builder.add_node("virtual_customer", virtual_customer_node)
    builder.add_node("simulation_round", safe_simulation_run)
    builder.add_node("review_3h", review_3h_node)

    # Phase 5 & 6
    builder.add_node("spec_generation", spec_generation_node)
    builder.add_node("experiment_planning", experiment_planning_node)
    builder.add_node("governance", governance_node)


def _register_edges(builder: WorkflowBuilder) -> None:
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


def _configure_interrupts(builder: WorkflowBuilder) -> None:
    """Configure human-in-the-loop interruption points."""
    interrupts = ["ideator", "vpc", "sitemap_wireframe", "virtual_customer", "experiment_planning"]
    builder.set_interrupts(interrupts)


def create_app() -> CompiledStateGraph[Any, Any]:
    """
    Create and compile the LangGraph application.
    This graph implements the "The JTC 2.0" architecture with documented HITL Gates.
    """
    builder = WorkflowBuilder()

    _register_nodes(builder)
    _register_edges(builder)
    _configure_interrupts(builder)

    return builder.build()
