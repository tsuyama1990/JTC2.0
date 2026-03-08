import logging
from typing import Any

from langgraph.graph import END, StateGraph
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
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)




def create_app() -> CompiledStateGraph[Any, Any]:
    """
    Create and compile the LangGraph application.

    This graph implements the "The JTC 2.0" architecture with documented HITL Gates.
    """
    workflow = StateGraph(GlobalState)

    # --- NODE DEFINITIONS ---
    workflow.add_node("ideator", safe_ideator_run)
    workflow.add_node("verification", verification_node)

    # Phase 2
    workflow.add_node("persona", persona_node)
    workflow.add_node("alternative_analysis", alternative_analysis_node)
    workflow.add_node("vpc", vpc_node)
    workflow.add_node("transcript_ingestion", transcript_ingestion_node)

    # Phase 3
    workflow.add_node("mental_model_journey", mental_model_journey_node)
    workflow.add_node("sitemap_wireframe", sitemap_wireframe_node)

    # Phase 4
    workflow.add_node("virtual_customer", virtual_customer_node)
    workflow.add_node("simulation_round", safe_simulation_run)
    workflow.add_node("review_3h", review_3h_node)

    # Phase 5 & 6
    workflow.add_node("spec_generation", spec_generation_node)
    workflow.add_node("experiment_planning", experiment_planning_node)
    workflow.add_node("governance", governance_node)

    # --- EDGE DEFINITIONS ---
    workflow.set_entry_point("ideator")

    # Gate 1: Idea Verification
    workflow.add_edge("ideator", "verification")
    workflow.add_edge("verification", "persona")
    workflow.add_edge("persona", "alternative_analysis")
    workflow.add_edge("alternative_analysis", "vpc")

    # Gate 1.5: CPF Feedback (Interrupt after VPC)
    workflow.add_edge("vpc", "transcript_ingestion")

    # Phase 3
    workflow.add_edge("transcript_ingestion", "mental_model_journey")
    workflow.add_edge("mental_model_journey", "sitemap_wireframe")

    # Gate 1.8: PSF Feedback (Interrupt after Sitemap)
    workflow.add_edge("sitemap_wireframe", "virtual_customer")

    # Gate 2: Virtual Market Pivot Decision (Interrupt after Virtual Customer)
    workflow.add_edge("virtual_customer", "simulation_round")

    workflow.add_edge("simulation_round", "review_3h")

    workflow.add_edge("review_3h", "spec_generation")
    workflow.add_edge("spec_generation", "experiment_planning")

    # Gate 3: Final Output FB (Interrupt after Experiment Plan)
    workflow.add_edge("experiment_planning", "governance")
    workflow.add_edge("governance", END)

    interrupts = [
        "ideator",
        "vpc",
        "sitemap_wireframe",
        "virtual_customer",
        "experiment_planning"
    ]

    # Validate interrupt sequence
    valid_nodes = set(workflow.nodes.keys())
    for node in interrupts:
        if node not in valid_nodes:
            msg = f"Invalid interrupt node configured: {node}"
            raise ValueError(msg)

    # Compile with Interrupts for documented HITL Gates
    return workflow.compile(interrupt_after=interrupts)
