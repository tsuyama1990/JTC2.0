import logging
from collections.abc import Callable
from typing import Any

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.core.interfaces import INodeRegistry
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


class NodeRegistry(INodeRegistry):
    def __init__(self) -> None:
        self._nodes: dict[str, Callable[[GlobalState], dict[str, Any]]] = {}

    def get_node(self, name: str) -> Any:
        if name not in self._nodes:
            msg = f"Node {name} not registered"
            raise ValueError(msg)
        return self._nodes[name]

    def register_node(self, name: str, func: Any) -> None:
        self._nodes[name] = func


def get_default_registry() -> INodeRegistry:
    """Creates a registry with the default application nodes."""
    from src.core.nodes import (
        alternative_analysis_node,
        experiment_planning_node,
        governance_node,
        mental_model_journey_node,
        persona_node,
        safe_ideator_run,
        safe_simulation_run,
        sitemap_wireframe_node,
        spec_generation_node,
        th_review_node,
        transcript_ingestion_node,
        verification_node,
        virtual_customer_node,
        vpc_node,
    )

    registry = NodeRegistry()
    registry.register_node("ideator", safe_ideator_run)
    registry.register_node("verification", verification_node)
    registry.register_node("persona", persona_node)
    registry.register_node("alternative_analysis", alternative_analysis_node)
    registry.register_node("vpc", vpc_node)
    registry.register_node("transcript_ingestion", transcript_ingestion_node)
    registry.register_node("mental_model_journey", mental_model_journey_node)
    registry.register_node("sitemap_wireframe", sitemap_wireframe_node)
    registry.register_node("virtual_customer", virtual_customer_node)
    registry.register_node("simulation_round", safe_simulation_run)
    registry.register_node("th_review", th_review_node)
    registry.register_node("spec_generation", spec_generation_node)
    registry.register_node("experiment_planning", experiment_planning_node)
    registry.register_node("governance", governance_node)

    return registry


def create_app(registry: INodeRegistry | None = None) -> CompiledStateGraph[Any, Any, Any]:
    """
    Create and compile the LangGraph application.

    This graph implements the "The JTC 2.0" architecture with 4 critical Decision Gates.
    """
    workflow = StateGraph(GlobalState)

    if registry is None:
        registry = get_default_registry()

    # --- NODE DEFINITIONS ---
    workflow.add_node("ideator", registry.get_node("ideator"))
    workflow.add_node("verification", registry.get_node("verification"))
    workflow.add_node("persona", registry.get_node("persona"))
    workflow.add_node("alternative_analysis", registry.get_node("alternative_analysis"))
    workflow.add_node("vpc", registry.get_node("vpc"))
    workflow.add_node("transcript_ingestion", registry.get_node("transcript_ingestion"))

    workflow.add_node("mental_model_journey", registry.get_node("mental_model_journey"))
    workflow.add_node("sitemap_wireframe", registry.get_node("sitemap_wireframe"))

    workflow.add_node("virtual_customer", registry.get_node("virtual_customer"))
    workflow.add_node("simulation_round", registry.get_node("simulation_round"))
    workflow.add_node("th_review", registry.get_node("th_review"))

    workflow.add_node("spec_generation", registry.get_node("spec_generation"))
    workflow.add_node("experiment_planning", registry.get_node("experiment_planning"))

    workflow.add_node("governance", registry.get_node("governance"))

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
