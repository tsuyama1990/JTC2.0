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


class WorkflowBuilder:
    """Builds the LangGraph application."""

    def __init__(self) -> None:
        self.workflow = StateGraph(GlobalState)

    def _register_nodes(self) -> None:
        self.workflow.add_node("ideator", safe_ideator_run)
        self.workflow.add_node("verification", verification_node)
        self.workflow.add_node("persona", persona_node)
        self.workflow.add_node("alternative_analysis", alternative_analysis_node)
        self.workflow.add_node("vpc", vpc_node)
        self.workflow.add_node("transcript_ingestion", transcript_ingestion_node)
        self.workflow.add_node("mental_model_journey", mental_model_journey_node)
        self.workflow.add_node("sitemap_wireframe", sitemap_wireframe_node)
        self.workflow.add_node("virtual_customer", virtual_customer_node)
        self.workflow.add_node("simulation_round", safe_simulation_run)
        self.workflow.add_node("review_3h", review_3h_node)
        self.workflow.add_node("spec_generation", spec_generation_node)
        self.workflow.add_node("experiment_planning", experiment_planning_node)
        self.workflow.add_node("governance", governance_node)

    def _register_edges(self) -> None:
        self.workflow.set_entry_point("ideator")
        self.workflow.add_edge("ideator", "verification")
        self.workflow.add_edge("verification", "persona")
        self.workflow.add_edge("persona", "alternative_analysis")
        self.workflow.add_edge("alternative_analysis", "vpc")
        self.workflow.add_edge("vpc", "transcript_ingestion")
        self.workflow.add_edge("transcript_ingestion", "mental_model_journey")
        self.workflow.add_edge("mental_model_journey", "sitemap_wireframe")
        self.workflow.add_edge("sitemap_wireframe", "virtual_customer")
        self.workflow.add_edge("virtual_customer", "simulation_round")
        self.workflow.add_edge("simulation_round", "review_3h")
        self.workflow.add_edge("review_3h", "spec_generation")
        self.workflow.add_edge("spec_generation", "experiment_planning")
        self.workflow.add_edge("experiment_planning", "governance")
        self.workflow.add_edge("governance", END)

    def build(self) -> CompiledStateGraph[Any, Any]:
        self._register_nodes()
        self._register_edges()

        interrupts = [
            "ideator",
            "vpc",
            "sitemap_wireframe",
            "virtual_customer",
            "experiment_planning",
        ]

        valid_nodes = set(self.workflow.nodes.keys())
        for node in interrupts:
            if node not in valid_nodes:
                msg = f"Invalid interrupt node configured: {node}"
                raise ValueError(msg)

        return self.workflow.compile(interrupt_after=interrupts)
