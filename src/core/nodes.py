import logging
import logging
from collections.abc import Callable
from typing import Any

from src.core.factory import AgentFactory
from src.core.interfaces import IAgent, IOutputGenerationAgent, IRemasteredAgent
from src.core.nemawashi.engine import NemawashiEngine
from src.core.node_executor import NodeExecutor
from src.core.services.pdf_generator import PDFGenerator
from src.core.simulation import create_simulation_graph
from src.core.workflow_builder import node_registry
from src.data.rag import RAG
from src.domain_models.simulation import Role
from src.domain_models.state import GlobalState, Phase
from src.domain_models.validators import StateValidator
from src.ui.renderer import ApprovalStampRenderer

logger = logging.getLogger(__name__)




class GraphNodeExecutor:
    """Executes nodes by injecting necessary agent dependencies and catching errors."""

    def __init__(self, agent: Any, node_name: str, settings: Any | None = None, file_service: Any | None = None) -> None:
        self.agent = agent
        self.node_name = node_name
        self.settings = settings
        self.file_service = file_service

    def ideator_run(self, state: GlobalState) -> dict[str, Any]:
        """Phase 1: Ideator Agent run."""
        def _impl(st: GlobalState) -> dict[str, Any]:
            res = self.agent.run(st)
            return res if isinstance(res, dict) else {}
        res = NodeExecutor.execute(_impl, state, f"Error in {self.node_name}")
        return res if isinstance(res, dict) else {}

    def persona_run(self, state: GlobalState) -> dict[str, Any]:
        def _impl(st: GlobalState) -> dict[str, Any]:
            logger.info("Generating Persona...")
            res = self.agent.generate_persona(st)
            return res if isinstance(res, dict) else {}
        res = NodeExecutor.execute(_impl, state, f"Error in {self.node_name}")
        return res if isinstance(res, dict) else {}

    def alternative_analysis_run(self, state: GlobalState) -> dict[str, Any]:
        def _impl(st: GlobalState) -> dict[str, Any]:
            logger.info("Generating Alternative Analysis...")
            updates = self.agent.generate_alternative_analysis(st)
            if updates.get("alternative_analysis"):
                PDFGenerator.generate_canvas_pdf(
                    updates["alternative_analysis"], "alternative_analysis.pdf"
                )
            return updates if isinstance(updates, dict) else {}
        res = NodeExecutor.execute(_impl, state, f"Error in {self.node_name}")
        return res if isinstance(res, dict) else {}

    def vpc_run(self, state: GlobalState) -> dict[str, Any]:
        def _impl(st: GlobalState) -> dict[str, Any]:
            logger.info("Generating Value Proposition Canvas...")
            updates = self.agent.generate_vpc(st)
            if updates.get("value_proposition"):
                PDFGenerator.generate_canvas_pdf(
                    updates["value_proposition"], "value_proposition_canvas.pdf"
                )
                ApprovalStampRenderer("VPC Canvas").start()
            return updates if isinstance(updates, dict) else {}
        res = NodeExecutor.execute(_impl, state, f"Error in {self.node_name}")
        return res if isinstance(res, dict) else {}

    def mental_model_journey_run(self, state: GlobalState) -> dict[str, Any]:
        def _impl(st: GlobalState) -> dict[str, Any]:
            logger.info("Generating Mental Model and Customer Journey...")
            updates = self.agent.generate_mental_model_and_journey(st)
            if updates.get("mental_model"):
                PDFGenerator.generate_canvas_pdf(updates["mental_model"], "mental_model_diagram.pdf")
            if updates.get("customer_journey"):
                PDFGenerator.generate_canvas_pdf(updates["customer_journey"], "customer_journey.pdf")

            if updates.get("mental_model") or updates.get("customer_journey"):
                ApprovalStampRenderer("Mental Model & Journey").start()
            return updates if isinstance(updates, dict) else {}
        res = NodeExecutor.execute(_impl, state, f"Error in {self.node_name}")
        return res if isinstance(res, dict) else {}

    def sitemap_wireframe_run(self, state: GlobalState) -> dict[str, Any]:
        def _impl(st: GlobalState) -> dict[str, Any]:
            logger.info("Generating Sitemap and User Story...")
            updates = self.agent.generate_sitemap_and_wireframe(st)
            if updates.get("sitemap_and_story"):
                PDFGenerator.generate_canvas_pdf(updates["sitemap_and_story"], "sitemap_and_story.pdf")
                ApprovalStampRenderer("Sitemap & Story").start()
            return updates if isinstance(updates, dict) else {}
        res = NodeExecutor.execute(_impl, state, f"Error in {self.node_name}")
        return res if isinstance(res, dict) else {}

    def spec_generation_run(self, state: GlobalState) -> dict[str, Any]:
        def _impl(st: GlobalState) -> dict[str, Any]:
            logger.info("Generating Agent Prompt Spec...")
            updates = self.agent.generate_agent_prompt_spec(st)
            if updates.get("agent_prompt_spec"):
                from src.core.utils import strip_html_tags

                spec = updates["agent_prompt_spec"]

                # Safe string formatting with sanitization for mermaid block
                safe_mermaid = strip_html_tags(spec.mermaid_flowchart)

                content = (
                    f"# Agent Prompt Specification\n\n"
                    f"## Core Story\n```json\n{spec.core_user_story.model_dump_json(indent=2)}\n```\n\n"
                    f"## State Machine\n```json\n{spec.state_machine.model_dump_json(indent=2)}\n```\n\n"
                    f"## State Machine (Mermaid)\n```mermaid\n{safe_mermaid}\n```\n"
                )

                if self.file_service:
                    self.file_service.save_canvas_output_async(content, "AgentPromptSpec.md")

                ApprovalStampRenderer("Agent Prompt Spec").start()
            return updates if isinstance(updates, dict) else {}
        res = NodeExecutor.execute(_impl, state, f"Error in {self.node_name}")
        return res if isinstance(res, dict) else {}

    def experiment_planning_run(self, state: GlobalState) -> dict[str, Any]:
        def _impl(st: GlobalState) -> dict[str, Any]:
            logger.info("Generating Experiment Plan...")
            updates = self.agent.generate_experiment_plan(st)
            if updates.get("experiment_plan"):
                PDFGenerator.generate_canvas_pdf(updates["experiment_plan"], "experiment_plan.pdf")

                content = f"# Experiment Plan\n\n```json\n{updates['experiment_plan'].model_dump_json(indent=2)}\n```\n"

                if self.file_service:
                    self.file_service.save_canvas_output_async(content, "ExperimentPlan.md")

                ApprovalStampRenderer("Experiment Plan").start()
            return updates if isinstance(updates, dict) else {}
        res = NodeExecutor.execute(_impl, state, f"Error in {self.node_name}")
        return res if isinstance(res, dict) else {}

    def virtual_customer_run(self, state: GlobalState) -> dict[str, Any]:
        def _impl(st: GlobalState) -> dict[str, Any]:
            logger.info("Running Virtual Customer Simulation...")
            res = self.agent.run(st)
            return res if isinstance(res, dict) else {}
        res = NodeExecutor.execute(_impl, state, f"Error in {self.node_name}")
        return res if isinstance(res, dict) else {}

    def review_3h_run(self, hacker_agent: IAgent, hipster_agent: IAgent, hustler_agent: IAgent, state: GlobalState) -> dict[str, Any]:
        def _impl(st: GlobalState) -> dict[str, Any]:
            logger.info("Running 3H Review...")

            # Run sequentially and accumulate messages
            state_updates: dict[str, Any] = {"debate_history": list(st.debate_history)}
            for a in [hacker_agent, hipster_agent, hustler_agent]:
                updates = a.run(st)
                if "debate_history" in updates:
                    state_updates["debate_history"].extend(
                        [
                            msg
                            for msg in updates["debate_history"]
                            if msg not in state_updates["debate_history"]
                        ]
                    )
                    st.debate_history = state_updates["debate_history"]

            return state_updates

        res = NodeExecutor.execute(_impl, state, f"Error in {self.node_name}")
        return res if isinstance(res, dict) else {}


def make_ideator_node(ideator_agent: IAgent) -> Callable[[GlobalState], dict[str, Any]]:
    executor = GraphNodeExecutor(ideator_agent, "Ideator Agent")
    return executor.ideator_run


def _verification_node_impl(state: GlobalState) -> dict[str, Any]:
    """
    Transition to Verification Phase.
    Here we prepare for the 'Mom Test' by setting the phase.
    The user will select the Riskiest Assumption (Gate 2) and provide transcripts.
    """
    StateValidator.validate_phase_requirements(state)

    if not state.selected_idea:
        logger.error("Attempted to enter Verification Phase without a selected idea.")

    logger.info(f"Transitioning to Phase: {Phase.VERIFICATION}")
    return {"phase": Phase.VERIFICATION}


def verification_node(state: GlobalState) -> dict[str, Any]:
    """Transition to Verification Phase."""
    return NodeExecutor.execute(_verification_node_impl, state, "Error in Verification Node")


def make_persona_node(agent: IRemasteredAgent) -> Callable[[GlobalState], dict[str, Any]]:
    executor = GraphNodeExecutor(agent, "Persona Node")
    return executor.persona_run


def make_alternative_analysis_node(agent: IRemasteredAgent) -> Callable[[GlobalState], dict[str, Any]]:
    executor = GraphNodeExecutor(agent, "Alternative Analysis Node")
    return executor.alternative_analysis_run


def make_vpc_node(agent: IRemasteredAgent) -> Callable[[GlobalState], dict[str, Any]]:
    executor = GraphNodeExecutor(agent, "VPC Node")
    return executor.vpc_run


def make_mental_model_journey_node(agent: IRemasteredAgent) -> Callable[[GlobalState], dict[str, Any]]:
    executor = GraphNodeExecutor(agent, "Mental Model & Journey Node")
    return executor.mental_model_journey_run


def make_sitemap_wireframe_node(agent: IRemasteredAgent) -> Callable[[GlobalState], dict[str, Any]]:
    executor = GraphNodeExecutor(agent, "Sitemap & Wireframe Node")
    return executor.sitemap_wireframe_run


def make_spec_generation_node(agent: IOutputGenerationAgent, file_service: Any | None = None) -> Callable[[GlobalState], dict[str, Any]]:
    executor = GraphNodeExecutor(agent, "Spec Generation Node", file_service=file_service)
    return executor.spec_generation_run


def make_experiment_planning_node(agent: IOutputGenerationAgent, file_service: Any | None = None) -> Callable[[GlobalState], dict[str, Any]]:
    executor = GraphNodeExecutor(agent, "Experiment Planning Node", file_service=file_service)
    return executor.experiment_planning_run


def make_virtual_customer_node(agent: IAgent) -> Callable[[GlobalState], dict[str, Any]]:
    executor = GraphNodeExecutor(agent, "Virtual Customer Node")
    return executor.virtual_customer_run


def make_review_3h_node(hacker_agent: IAgent, hipster_agent: IAgent, hustler_agent: IAgent) -> Callable[[GlobalState], dict[str, Any]]:
    executor = GraphNodeExecutor(None, "3H Review Node")
    import functools
    return functools.partial(executor.review_3h_run, hacker_agent, hipster_agent, hustler_agent)

# We don't register globally here anymore; DI is handled in `GraphBuilderService`.


def _validate_transcripts(state: GlobalState) -> None:
    if not state.transcripts:
        msg = "No transcripts found in state to ingest. Missing validation."
        raise ValueError(msg)


def _ingest_impl(state: GlobalState, settings: Any) -> dict[str, Any]:

    rag = RAG(persist_dir=state.rag_index_path)

    max_transcripts = settings.rag.max_transcripts
    chunk_size = settings.rag.batch_size

    transcript_iter = iter(state.transcripts)

    processed_count = 0
    try:
        while processed_count < max_transcripts:
            from itertools import islice

            chunk = list(islice(transcript_iter, chunk_size))
            if not chunk:
                break

            logger.info(
                f"Ingesting batch {(processed_count // chunk_size) + 1}: {len(chunk)} transcripts"
            )
            for transcript in chunk:
                rag.ingest_transcript(transcript)

            processed_count += len(chunk)

        rag.persist_index()

        if next(transcript_iter, None) is not None:
            logger.warning(
                f"Exceeded MAX_TRANSCRIPTS ({max_transcripts}). Remaining transcripts ignored to prevent OOM."
            )
    except Exception as e:
        logger.exception("Error during RAG ingestion")
        # Return state unchanged, possibly with an error message later
        # But prevent total crash
        msg = f"RAG ingestion failed: {e}"
        raise ValueError(msg) from e

    return {}


def make_transcript_ingestion_node(settings: Any) -> Callable[[GlobalState], dict[str, Any]]:
    def _transcript_ingestion_node_impl(state: GlobalState) -> dict[str, Any]:
        """
        Ingest customer transcripts into the RAG system.
        Runs after Gate 2 (User Input of Transcript).
        """
        logger.info("Ingesting transcripts into RAG...")
        _validate_transcripts(state)
        return _ingest_impl(state, settings)

    def transcript_ingestion_node(state: GlobalState) -> dict[str, Any]:
        return NodeExecutor.execute(
            _transcript_ingestion_node_impl, state, "Error during transcript ingestion"
        )
    return transcript_ingestion_node

# We don't register globally here anymore; DI is handled in `GraphBuilderService`.


def _transform_simulation_state(final_state: Any) -> dict[str, Any]:
    if isinstance(final_state, dict):
        return {"debate_history": final_state.get("debate_history", [])}
    if hasattr(final_state, "debate_history"):
        return {"debate_history": final_state.debate_history}

    logger.warning("Simulation graph returned unknown state type.")
    return {}


def make_simulation_node(simulation_app: Any) -> Callable[[GlobalState], dict[str, Any]]:
    def _safe_simulation_run_impl(state: GlobalState) -> dict[str, Any]:
        """
        Wrapper for Simulation execution with error handling.
        Runs the full turn-based simulation (Finance vs Sales vs New Employee).
        """
        logger.info("Starting Simulation Round (Turn-based Battle)")

        final_state = simulation_app.invoke(state)
        return _transform_simulation_state(final_state)

    def safe_simulation_run(state: GlobalState) -> dict[str, Any]:
        return NodeExecutor.execute(_safe_simulation_run_impl, state, "Error in Simulation Graph")
    return safe_simulation_run


def _identify_and_log_influencers(engine: NemawashiEngine, network: Any) -> None:
    influencers = engine.identify_influencers(network)
    logger.info(f"Identified Key Influencers: {influencers}")


def make_nemawashi_analysis_node(engine_factory: Callable[[], NemawashiEngine] | None = None) -> Callable[[GlobalState], dict[str, Any]]:
    def _nemawashi_analysis_node_impl(state: GlobalState) -> dict[str, Any]:
        """
        Run Nemawashi (Consensus) analysis after the simulation.
        Updates the influence network with new opinion dynamics.
        """
        logger.info("Running Nemawashi Consensus Analysis...")

        if not state.influence_network:
            logger.warning("No influence network found. Skipping Nemawashi analysis.")
            return {}

        if engine_factory is not None:
            engine = engine_factory()
        else:

            from src.core.nemawashi.analytics import InfluenceAnalyzer
            from src.core.nemawashi.consensus import ConsensusEngine
            from src.core.nemawashi.engine import NemawashiEngine
            from src.core.nemawashi.nomikai import NomikaiSimulator

            settings = get_settings().nemawashi
            consensus = ConsensusEngine(settings)
            analytics = InfluenceAnalyzer(settings.analytics_cache_size)
            simulator = NomikaiSimulator(settings)
            engine = NemawashiEngine(consensus, analytics, simulator, settings)

        # Calculate new consensus (opinions)
        new_opinions = engine.calculate_consensus(state.influence_network)

        # Update the influence network in state
        updated_network = state.influence_network.model_copy(deep=True)

        for i, stakeholder in enumerate(updated_network.stakeholders):
            if i < len(new_opinions):
                stakeholder.initial_support = new_opinions[i]

        _identify_and_log_influencers(engine, updated_network)

        return {"influence_network": updated_network}

    def nemawashi_analysis_node(state: GlobalState) -> dict[str, Any]:
        return NodeExecutor.execute(_nemawashi_analysis_node_impl, state, "Error in Nemawashi Analysis")
    return nemawashi_analysis_node

# We don't register globally here anymore; DI is handled in `GraphBuilderService`.


def make_cpo_node(cpo_agent: IAgent) -> Callable[[GlobalState], dict[str, Any]]:
    def _cpo_run_impl(state: GlobalState) -> dict[str, Any]:
        """Wrapper for CPO execution with error handling."""
        result = cpo_agent.run(state)
        if isinstance(result, dict):
            return result
        return {}

    def safe_cpo_run(state: GlobalState) -> dict[str, Any]:
        return NodeExecutor.execute(_cpo_run_impl, state, "Error in CPO Agent")
    return safe_cpo_run


def _transition_phase(updates: dict[str, Any], phase: Phase) -> dict[str, Any]:
    updates["phase"] = phase
    return updates


def make_governance_node(agent: IAgent) -> Callable[[GlobalState], dict[str, Any]]:
    def _governance_node_impl(state: GlobalState) -> dict[str, Any]:
        """
        Run Governance Agent for Cycle 6 (Ringi-sho).
        """
        logger.info("Running Governance Check...")

        updates = agent.run(state)

        return _transition_phase(updates, Phase.GOVERNANCE)

    def governance_node(state: GlobalState) -> dict[str, Any]:
        return NodeExecutor.execute(_governance_node_impl, state, "Error in Governance Check")
    return governance_node

# We don't register globally here anymore; DI is handled in `GraphBuilderService`.


