from src.core.config import Settings
import logging
from typing import Any

from langgraph.graph import END
from langgraph.graph.state import CompiledStateGraph

from src.core.workflow_builder import WorkflowBuilder, WorkflowRegistry
from src.domain_models.state import GlobalState

logger = logging.getLogger(__name__)




from src.core.config import Settings
from src.core.factory import AgentFactory

class GraphBuilderService:
    """Builds the execution graph directly injecting nodes instead of relying on a global registry."""

    def __init__(self, settings: Settings, agent_factory: AgentFactory) -> None:
        self.settings = settings
        self.agent_factory = agent_factory

    def _register_nodes(self, builder: WorkflowBuilder[GlobalState]) -> WorkflowBuilder[GlobalState]:
        """Register all nodes into the workflow builder manually injecting dependencies."""
        from src.core.nodes import (
            make_alternative_analysis_node,
            make_experiment_planning_node,
            make_governance_node,
            make_ideator_node,
            make_mental_model_journey_node,
            make_nemawashi_analysis_node,
            make_persona_node,
            make_review_3h_node,
            make_sitemap_wireframe_node,
            make_spec_generation_node,
            make_transcript_ingestion_node,
            make_virtual_customer_node,
            make_vpc_node,
            make_simulation_node,
            verification_node,
        )

        current_builder = builder

        current_builder = current_builder.add_node("ideator", make_ideator_node(self.agent_factory.get_ideator_agent()))
        current_builder = current_builder.add_node("verification", verification_node)
        current_builder = current_builder.add_node("persona", make_persona_node(self.agent_factory.get_remastered_agent()))
        current_builder = current_builder.add_node("alternative_analysis", make_alternative_analysis_node(self.agent_factory.get_remastered_agent()))
        current_builder = current_builder.add_node("vpc", make_vpc_node(self.agent_factory.get_remastered_agent()))
        current_builder = current_builder.add_node("transcript_ingestion", make_transcript_ingestion_node(self.settings))
        current_builder = current_builder.add_node("mental_model_journey", make_mental_model_journey_node(self.agent_factory.get_remastered_agent()))
        current_builder = current_builder.add_node("sitemap_wireframe", make_sitemap_wireframe_node(self.agent_factory.get_remastered_agent()))
        current_builder = current_builder.add_node("virtual_customer", make_virtual_customer_node(self.agent_factory.get_virtual_customer_agent()))

        from src.core.simulation import create_simulation_graph
        simulation_app = create_simulation_graph(self.settings)
        current_builder = current_builder.add_node("simulation_round", make_simulation_node(simulation_app))

        current_builder = current_builder.add_node("review_3h", make_review_3h_node(
            self.agent_factory.get_hacker_agent(),
            self.agent_factory.get_hipster_agent(),
            self.agent_factory.get_hustler_agent()
        ))

        from src.core.services.file_service import FileService
        file_service = FileService(settings=self.settings)
        current_builder = current_builder.add_node("spec_generation", make_spec_generation_node(self.agent_factory.get_output_generation_agent(), file_service))
        current_builder = current_builder.add_node("experiment_planning", make_experiment_planning_node(self.agent_factory.get_output_generation_agent(), file_service))
        current_builder = current_builder.add_node("governance", make_governance_node(self.agent_factory.get_governance_agent()))

        # We don't use nemawashi explicitly in default edge path but we register it here
        from src.core.nemawashi.analytics import InfluenceAnalyzer
        from src.core.nemawashi.consensus import ConsensusEngine
        from src.core.nemawashi.engine import NemawashiEngine
        from src.core.nemawashi.nomikai import NomikaiSimulator

        def create_engine() -> NemawashiEngine:
            nema_settings = self.settings.nemawashi
            consensus = ConsensusEngine(nema_settings)
            analytics = InfluenceAnalyzer(nema_settings.analytics_cache_size)
            simulator = NomikaiSimulator(nema_settings)
            return NemawashiEngine(consensus, analytics, simulator, nema_settings)

        current_builder = current_builder.add_node("nemawashi_analysis", make_nemawashi_analysis_node(create_engine))

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
        current_builder = builder if builder is not None else WorkflowBuilder[GlobalState](GlobalState)
        current_builder = self._register_nodes(current_builder)
        current_builder = self._register_edges(current_builder)
        current_builder = self._configure_interrupts(current_builder)
        return current_builder.build()


def create_app(
    settings: Settings,
    agent_factory: AgentFactory,
    builder: WorkflowBuilder[GlobalState] | None = None,
) -> CompiledStateGraph[Any, Any]:
    """
    Create and compile the LangGraph application.
    This graph implements the "The JTC 2.0" architecture with documented HITL Gates.
    """
    try:
        service = GraphBuilderService(settings, agent_factory)
        return service.build_graph(builder)
    except Exception as e:
        logger.error(f"Failed to build application graph: {e}")
        raise RuntimeError(f"Workflow initialization failed: {e}") from e
