import logging

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.core.nodes import (
    governance_node,
    mvp_generation_node,
    nemawashi_analysis_node,
    pmf_node,
    safe_cpo_run,
    safe_ideator_run,
    safe_simulation_run,
    solution_proposal_node,
    transcript_ingestion_node,
    verification_node,
)
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


def create_app() -> CompiledStateGraph:  # type: ignore[type-arg]
    """
    Create and compile the LangGraph application.

    This graph implements the "The JTC 2.0" architecture with 4 critical Decision Gates.
    """
    workflow = StateGraph(GlobalState)

    # --- NODE DEFINITIONS ---
    workflow.add_node("ideator", safe_ideator_run)
    workflow.add_node("verification", verification_node)
    workflow.add_node("transcript_ingestion", transcript_ingestion_node)
    workflow.add_node("simulation_round", safe_simulation_run)
    workflow.add_node("nemawashi_analysis", nemawashi_analysis_node)
    workflow.add_node("cpo_mentoring", safe_cpo_run)
    workflow.add_node("solution_proposal", solution_proposal_node)
    workflow.add_node("mvp_generation", mvp_generation_node)
    workflow.add_node("pmf", pmf_node)
    workflow.add_node("governance", governance_node)

    # --- EDGE DEFINITIONS ---
    workflow.set_entry_point("ideator")

    # Gate 1: Idea Verification (Plan A Selection)
    # Interrupt happens after 'ideator' returns.
    workflow.add_edge("ideator", "verification")

    # Gate 2: Customer-Problem Fit (Riskiest Assumption)
    # Interrupt happens after 'verification' returns.
    # User provides transcript during resume.
    workflow.add_edge("verification", "transcript_ingestion")

    # Process transcript then start simulation
    workflow.add_edge("transcript_ingestion", "simulation_round")

    # Simulation -> Nemawashi Analysis -> CPO Mentoring
    workflow.add_edge("simulation_round", "nemawashi_analysis")
    workflow.add_edge("nemawashi_analysis", "cpo_mentoring")

    # Gate 3: Problem-Solution Fit (MVP Scope)
    # CPO advises -> Solution proposed (Features extracted) -> Interrupt for selection
    workflow.add_edge("cpo_mentoring", "solution_proposal")
    workflow.add_edge("solution_proposal", "mvp_generation")

    # MVP Generated -> PMF Check
    workflow.add_edge("mvp_generation", "pmf")

    # Gate 4: Product-Market Fit (Pivot Decision)
    # Interrupt happens after 'pmf' returns.
    # User validates PMF, then we proceed to Governance.
    workflow.add_edge("pmf", "governance")

    # Governance -> End (Report generated)
    workflow.add_edge("governance", END)

    # Compile with Interrupts for HITL Gates
    return workflow.compile(
        interrupt_after=[
            "ideator",
            "verification",
            "solution_proposal",
            "pmf"
        ]
    )
