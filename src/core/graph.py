import logging
from typing import Any

from langgraph.graph import END
from langgraph.graph.state import CompiledStateGraph

from src.core.workflow_builder import WorkflowBuilder, WorkflowRegistry
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)


class GraphBuilderService:
    def __init__(self, registry: WorkflowRegistry[GlobalState]) -> None:
        self.registry = registry

    def _register_nodes(self, builder: WorkflowBuilder[GlobalState]) -> WorkflowBuilder[GlobalState]:
        """Register all nodes into the workflow builder using the registry."""
        import src.core.nodes
        from src.core.config import get_settings

        # In a real environment, we'd inject dependencies properly. For now, since tests
        # or runtime might not have all nodes registered via `@node_registry.register`,
        # we manually create and add the required nodes if they are missing from the registry.
        # We need to make sure the core factory is initialized
        from src.core.factory import AgentFactory
        from src.core.llm import LLMFactory

        settings = get_settings()
        llm = LLMFactory().get_llm()
        factory = AgentFactory(llm=llm, settings=settings)

        # Register node if not already in registry
        if "ideator" not in self.registry.nodes:
            self.registry.nodes["ideator"] = src.core.nodes.make_ideator_node(factory.get_ideator_agent())
        if "persona" not in self.registry.nodes:
            self.registry.nodes["persona"] = src.core.nodes.make_persona_node(factory.get_remastered_agent())
        if "alternative_analysis" not in self.registry.nodes:
            self.registry.nodes["alternative_analysis"] = src.core.nodes.make_alternative_analysis_node(factory.get_remastered_agent())
        if "vpc" not in self.registry.nodes:
            self.registry.nodes["vpc"] = src.core.nodes.make_vpc_node(factory.get_remastered_agent())
        if "mental_model_journey" not in self.registry.nodes:
            self.registry.nodes["mental_model_journey"] = src.core.nodes.make_mental_model_journey_node(factory.get_remastered_agent())
        if "sitemap_wireframe" not in self.registry.nodes:
            self.registry.nodes["sitemap_wireframe"] = src.core.nodes.make_sitemap_wireframe_node(factory.get_remastered_agent())
        if "virtual_customer" not in self.registry.nodes:
            self.registry.nodes["virtual_customer"] = src.core.nodes.make_virtual_customer_node(factory.get_virtual_customer_agent())
        if "review_3h" not in self.registry.nodes:
            self.registry.nodes["review_3h"] = src.core.nodes.make_review_3h_node(
                factory.get_hacker_agent(), factory.get_hipster_agent(), factory.get_hustler_agent()
            )
        if "spec_generation" not in self.registry.nodes:
            self.registry.nodes["spec_generation"] = src.core.nodes.make_spec_generation_node(factory.get_output_generation_agent())
        if "experiment_planning" not in self.registry.nodes:
            self.registry.nodes["experiment_planning"] = src.core.nodes.make_experiment_planning_node(factory.get_output_generation_agent())
        if "governance" not in self.registry.nodes:
            self.registry.nodes["governance"] = src.core.nodes.make_governance_node(factory.get_governance_agent())
        if "transcript_ingestion" not in self.registry.nodes:
            self.registry.nodes["transcript_ingestion"] = src.core.nodes.make_transcript_ingestion_node()
        if "simulation_round" not in self.registry.nodes:
            self.registry.nodes["simulation_round"] = src.core.nodes.safe_simulation_run

        current_builder = builder
        for name, func in self.registry.nodes.items():
            current_builder = current_builder.add_node(name, func)
        return current_builder

    def _register_edges(self, builder: WorkflowBuilder[GlobalState]) -> WorkflowBuilder[GlobalState]:
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

    def _configure_interrupts(self, builder: WorkflowBuilder[GlobalState]) -> WorkflowBuilder[GlobalState]:
        """Configure human-in-the-loop interruption points."""
        interrupts = ["ideator", "vpc", "sitemap_wireframe", "virtual_customer", "experiment_planning"]
        return builder.set_interrupts(interrupts)

    def build_graph(self, builder: WorkflowBuilder[GlobalState] | None = None) -> CompiledStateGraph[Any, Any]:
        if builder is None:
            builder = WorkflowBuilder[GlobalState](GlobalState)
        builder = self._register_nodes(builder)
        builder = self._register_edges(builder)
        builder = self._configure_interrupts(builder)
        return builder.build()


def create_app(
    registry: WorkflowRegistry[GlobalState],
    builder: WorkflowBuilder[GlobalState] | None = None,
) -> CompiledStateGraph[Any, Any]:
    """
    Create and compile the LangGraph application.
    This graph implements the "The JTC 2.0" architecture with documented HITL Gates.
    """
    service = GraphBuilderService(registry)
    return service.build_graph(builder)
