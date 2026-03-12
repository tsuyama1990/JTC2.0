import logging
from typing import Any

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.core.nodes import (
    alternative_analysis_node,
    governance_node,
    persona_node,
    safe_ideator_run,
    safe_simulation_run,
    transcript_ingestion_node,
    verification_node,
    vpc_node,
)
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


def create_app() -> CompiledStateGraph[Any, Any, Any]:
    """
    Create and compile the LangGraph application.

    This graph implements the "The JTC 2.0" architecture with 4 critical Decision Gates.
    """
    workflow = StateGraph(GlobalState)

    # --- NODE DEFINITIONS ---
    workflow.add_node("ideator", safe_ideator_run)
    workflow.add_node("verification", verification_node)
    workflow.add_node("persona", persona_node)
    workflow.add_node("alternative_analysis", alternative_analysis_node)
    workflow.add_node("vpc", vpc_node)
    workflow.add_node("transcript_ingestion", transcript_ingestion_node)

    # New Phase 3 Nodes
    from src.core.nodes import mental_model_journey_node, sitemap_wireframe_node

    workflow.add_node("mental_model_journey", mental_model_journey_node)
    workflow.add_node("sitemap_wireframe", sitemap_wireframe_node)

    # New Phase 4 Nodes
    from src.core.nodes import th_review_node, virtual_customer_node

    workflow.add_node("virtual_customer", virtual_customer_node)
    workflow.add_node("simulation_round", safe_simulation_run)
    workflow.add_node("th_review", th_review_node)

    # New Phase 5 & 6 Nodes
    from src.core.nodes import experiment_planning_node, spec_generation_node

    workflow.add_node("spec_generation", spec_generation_node)
    workflow.add_node("experiment_planning", experiment_planning_node)

    workflow.add_node("governance", governance_node)

    # --- EDGE DEFINITIONS ---
    workflow.set_entry_point("ideator")

    # Gate 1: Idea Verification (Plan A Selection)
    workflow.add_edge("ideator", "verification")

    workflow.add_edge("verification", "persona")
    workflow.add_edge("persona", "alternative_analysis")
    workflow.add_edge("alternative_analysis", "vpc")

    # Gate 1.5: Customer-Problem Fit (VPC Feedback)
    workflow.add_edge("vpc", "transcript_ingestion")

    # Phase 3
    workflow.add_edge("transcript_ingestion", "mental_model_journey")
    workflow.add_edge("mental_model_journey", "sitemap_wireframe")

    # Gate 1.8: Problem-Solution Fit (Sitemap Feedback)
    workflow.add_edge("sitemap_wireframe", "virtual_customer")

    # Gate 2: Virtual Customer Interview
    workflow.add_edge("virtual_customer", "simulation_round")

    # Phase 4
    workflow.add_edge("simulation_round", "th_review")

    # Phase 5 & 6
    workflow.add_edge("th_review", "spec_generation")
    workflow.add_edge("spec_generation", "experiment_planning")

    # Gate 3: Final Output Feedback
    workflow.add_edge("experiment_planning", "governance")

    # Governance -> End (Report generated)
    workflow.add_edge("governance", END)

    from src.core.config import get_settings

    settings = get_settings()

    # Compile with Interrupts for HITL Gates
    try:
        return workflow.compile(interrupt_after=settings.hitl_interrupt_nodes)
    except Exception as e:
        logger.exception("Failed to compile LangGraph workflow.")
        msg = "Workflow compilation failed. Please check graph configuration."
        raise RuntimeError(msg) from e
