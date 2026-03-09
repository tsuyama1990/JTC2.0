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




def make_ideator_node(ideator_agent: IAgent) -> Callable[[GlobalState], dict[str, Any]]:
    def _ideator_run_impl(state: GlobalState) -> dict[str, Any]:
        res = ideator_agent.run(state)
        return res if isinstance(res, dict) else {}

    def safe_ideator_run(state: GlobalState) -> dict[str, Any]:
        """Wrapper for Ideator execution with error handling."""
        res = NodeExecutor.execute(_ideator_run_impl, state, "Error in Ideator Agent")
        return res if isinstance(res, dict) else {}

    return safe_ideator_run


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

node_registry.register("verification")(verification_node)


def make_persona_node(agent: IRemasteredAgent) -> Callable[[GlobalState], dict[str, Any]]:
    def _persona_node_impl(state: GlobalState) -> dict[str, Any]:
        """Phase 2: Generate Persona."""
        logger.info("Generating Persona...")
        res = agent.generate_persona(state)
        return res if isinstance(res, dict) else {}

    def persona_node(state: GlobalState) -> dict[str, Any]:
        res = NodeExecutor.execute(_persona_node_impl, state, "Error in Persona Node")
        return res if isinstance(res, dict) else {}
    return persona_node


def make_alternative_analysis_node(agent: IRemasteredAgent) -> Callable[[GlobalState], dict[str, Any]]:
    def _alternative_analysis_node_impl(state: GlobalState) -> dict[str, Any]:
        """Phase 2: Generate Alternative Analysis."""
        logger.info("Generating Alternative Analysis...")
        updates = agent.generate_alternative_analysis(state)
        if updates.get("alternative_analysis"):
            PDFGenerator.generate_canvas_pdf(
                updates["alternative_analysis"], "alternative_analysis.pdf"
            )
        return updates if isinstance(updates, dict) else {}

    def alternative_analysis_node(state: GlobalState) -> dict[str, Any]:
        res = NodeExecutor.execute(
            _alternative_analysis_node_impl, state, "Error in Alternative Analysis Node"
        )
        return res if isinstance(res, dict) else {}
    return alternative_analysis_node


def make_vpc_node(agent: IRemasteredAgent) -> Callable[[GlobalState], dict[str, Any]]:
    def _vpc_node_impl(state: GlobalState) -> dict[str, Any]:
        """Phase 2: Generate Value Proposition Canvas."""
        logger.info("Generating Value Proposition Canvas...")
        updates = agent.generate_vpc(state)
        if updates.get("value_proposition"):
            PDFGenerator.generate_canvas_pdf(
                updates["value_proposition"], "value_proposition_canvas.pdf"
            )
            ApprovalStampRenderer("VPC Canvas").start()
        return updates if isinstance(updates, dict) else {}

    def vpc_node(state: GlobalState) -> dict[str, Any]:
        res = NodeExecutor.execute(_vpc_node_impl, state, "Error in VPC Node")
        return res if isinstance(res, dict) else {}
    return vpc_node


def make_mental_model_journey_node(agent: IRemasteredAgent) -> Callable[[GlobalState], dict[str, Any]]:
    def _mental_model_journey_node_impl(state: GlobalState) -> dict[str, Any]:
        """Phase 3: Generate Mental Model & Customer Journey."""
        logger.info("Generating Mental Model and Customer Journey...")
        updates = agent.generate_mental_model_and_journey(state)
        if updates.get("mental_model"):
            PDFGenerator.generate_canvas_pdf(updates["mental_model"], "mental_model_diagram.pdf")
        if updates.get("customer_journey"):
            PDFGenerator.generate_canvas_pdf(updates["customer_journey"], "customer_journey.pdf")

        if updates.get("mental_model") or updates.get("customer_journey"):
            ApprovalStampRenderer("Mental Model & Journey").start()
        return updates if isinstance(updates, dict) else {}

    def mental_model_journey_node(state: GlobalState) -> dict[str, Any]:
        res = NodeExecutor.execute(
            _mental_model_journey_node_impl, state, "Error in Mental Model & Journey Node"
        )
        return res if isinstance(res, dict) else {}
    return mental_model_journey_node


def make_sitemap_wireframe_node(agent: IRemasteredAgent) -> Callable[[GlobalState], dict[str, Any]]:
    def _sitemap_wireframe_node_impl(state: GlobalState) -> dict[str, Any]:
        """Phase 3: Generate Sitemap and Wireframe (User Story)."""
        logger.info("Generating Sitemap and User Story...")
        updates = agent.generate_sitemap_and_wireframe(state)
        if updates.get("sitemap_and_story"):
            PDFGenerator.generate_canvas_pdf(updates["sitemap_and_story"], "sitemap_and_story.pdf")
            ApprovalStampRenderer("Sitemap & Story").start()
        return updates if isinstance(updates, dict) else {}

    def sitemap_wireframe_node(state: GlobalState) -> dict[str, Any]:
        res = NodeExecutor.execute(
            _sitemap_wireframe_node_impl, state, "Error in Sitemap & Wireframe Node"
        )
        return res if isinstance(res, dict) else {}
    return sitemap_wireframe_node


def make_spec_generation_node(agent: IOutputGenerationAgent) -> Callable[[GlobalState], dict[str, Any]]:
    def _spec_generation_node_impl(state: GlobalState) -> dict[str, Any]:
        """Phase 5: Generate Agent Prompt Spec."""
        logger.info("Generating Agent Prompt Spec...")
        updates = agent.generate_agent_prompt_spec(state)
        if updates.get("agent_prompt_spec"):
            from pathlib import Path

            from src.core.config import get_settings

            settings = get_settings()
            output_dir = Path(settings.canvas_output_dir)
            if not output_dir.is_absolute():
                output_dir = Path.cwd() / output_dir
            output_dir.mkdir(parents=True, exist_ok=True)

            from src.core.services.file_service import FileService
            from src.core.utils import strip_html_tags

            target_path = output_dir / "AgentPromptSpec.md"
            spec = updates["agent_prompt_spec"]

            # Safe string formatting with sanitization for mermaid block
            safe_mermaid = strip_html_tags(spec.mermaid_flowchart)

            content = (
                f"# Agent Prompt Specification\n\n"
                f"## Core Story\n```json\n{spec.core_user_story.model_dump_json(indent=2)}\n```\n\n"
                f"## State Machine\n```json\n{spec.state_machine.model_dump_json(indent=2)}\n```\n\n"
                f"## State Machine (Mermaid)\n```mermaid\n{safe_mermaid}\n```\n"
            )

            file_service = FileService()
            file_service.save_text_async(content, target_path)

            ApprovalStampRenderer("Agent Prompt Spec").start()
        return updates if isinstance(updates, dict) else {}

    def spec_generation_node(state: GlobalState) -> dict[str, Any]:
        res = NodeExecutor.execute(
            _spec_generation_node_impl, state, "Error in Spec Generation Node"
        )
        return res if isinstance(res, dict) else {}
    return spec_generation_node


def make_experiment_planning_node(agent: IOutputGenerationAgent) -> Callable[[GlobalState], dict[str, Any]]:
    def _experiment_planning_node_impl(state: GlobalState) -> dict[str, Any]:
        """Phase 6: Generate Experiment Plan."""
        logger.info("Generating Experiment Plan...")
        updates = agent.generate_experiment_plan(state)
        if updates.get("experiment_plan"):
            PDFGenerator.generate_canvas_pdf(updates["experiment_plan"], "experiment_plan.pdf")
            from pathlib import Path

            from src.core.config import get_settings

            settings = get_settings()
            output_dir = Path(settings.canvas_output_dir)
            if not output_dir.is_absolute():
                output_dir = Path.cwd() / output_dir
            output_dir.mkdir(parents=True, exist_ok=True)
            from src.core.services.file_service import FileService

            target_path = output_dir / "ExperimentPlan.md"

            content = f"# Experiment Plan\n\n```json\n{updates['experiment_plan'].model_dump_json(indent=2)}\n```\n"

            file_service = FileService()
            file_service.save_text_async(content, target_path)

            ApprovalStampRenderer("Experiment Plan").start()
        return updates if isinstance(updates, dict) else {}

    def experiment_planning_node(state: GlobalState) -> dict[str, Any]:
        res = NodeExecutor.execute(
            _experiment_planning_node_impl, state, "Error in Experiment Planning Node"
        )
        return res if isinstance(res, dict) else {}
    return experiment_planning_node

# We don't register globally here anymore; DI is handled in `GraphBuilderService`.


def make_virtual_customer_node(agent: IAgent) -> Callable[[GlobalState], dict[str, Any]]:
    def _virtual_customer_node_impl(state: GlobalState) -> dict[str, Any]:
        """Phase 4: Virtual Customer Interview."""
        logger.info("Running Virtual Customer Simulation...")
        res = agent.run(state)
        return res if isinstance(res, dict) else {}

    def virtual_customer_node(state: GlobalState) -> dict[str, Any]:
        res = NodeExecutor.execute(
            _virtual_customer_node_impl, state, "Error in Virtual Customer Node"
        )
        return res if isinstance(res, dict) else {}
    return virtual_customer_node

# We don't register globally here anymore; DI is handled in `GraphBuilderService`.


def make_review_3h_node(hacker_agent: IAgent, hipster_agent: IAgent, hustler_agent: IAgent) -> Callable[[GlobalState], dict[str, Any]]:
    def _review_3h_node_impl(state: GlobalState) -> dict[str, Any]:
        """Phase 4: 3H Review (Hacker, Hipster, Hustler)."""
        logger.info("Running 3H Review...")

        # Run sequentially and accumulate messages
        state_updates: dict[str, Any] = {"debate_history": list(state.debate_history)}
        for a in [hacker_agent, hipster_agent, hustler_agent]:
            updates = a.run(state)
            if "debate_history" in updates:
                state_updates["debate_history"].extend(
                    [
                        msg
                        for msg in updates["debate_history"]
                        if msg not in state_updates["debate_history"]
                    ]
                )
                state.debate_history = state_updates["debate_history"]

        return state_updates

    def review_3h_node(state: GlobalState) -> dict[str, Any]:
        res = NodeExecutor.execute(_review_3h_node_impl, state, "Error in 3H Review Node")
        return res if isinstance(res, dict) else {}
    return review_3h_node

# We don't register globally here anymore; DI is handled in `GraphBuilderService`.


def _validate_transcripts(state: GlobalState) -> None:
    if not state.transcripts:
        msg = "No transcripts found in state to ingest. Missing validation."
        raise ValueError(msg)


def _ingest_impl(state: GlobalState) -> dict[str, Any]:
    from src.core.config import get_settings
    settings = get_settings()

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


def make_transcript_ingestion_node() -> Callable[[GlobalState], dict[str, Any]]:
    def _transcript_ingestion_node_impl(state: GlobalState) -> dict[str, Any]:
        """
        Ingest customer transcripts into the RAG system.
        Runs after Gate 2 (User Input of Transcript).
        """
        logger.info("Ingesting transcripts into RAG...")
        _validate_transcripts(state)
        return _ingest_impl(state)

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


def _safe_simulation_run_impl(state: GlobalState) -> dict[str, Any]:
    """
    Wrapper for Simulation execution with error handling.
    Runs the full turn-based simulation (Finance vs Sales vs New Employee).
    """
    logger.info("Starting Simulation Round (Turn-based Battle)")

    simulation_app = create_simulation_graph()
    final_state = simulation_app.invoke(state)
    return _transform_simulation_state(final_state)


def safe_simulation_run(state: GlobalState) -> dict[str, Any]:
    return NodeExecutor.execute(_safe_simulation_run_impl, state, "Error in Simulation Graph")


def _identify_and_log_influencers(engine: NemawashiEngine, network: Any) -> None:
    influencers = engine.identify_influencers(network)
    logger.info(f"Identified Key Influencers: {influencers}")


def make_nemawashi_analysis_node(engine_factory: Callable[[], NemawashiEngine]) -> Callable[[GlobalState], dict[str, Any]]:
    def _nemawashi_analysis_node_impl(state: GlobalState) -> dict[str, Any]:
        """
        Run Nemawashi (Consensus) analysis after the simulation.
        Updates the influence network with new opinion dynamics.
        """
        logger.info("Running Nemawashi Consensus Analysis...")

        if not state.influence_network:
            logger.warning("No influence network found. Skipping Nemawashi analysis.")
            return {}

        engine = engine_factory()

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


def _create_cpo_agent(state: GlobalState) -> Any:
    from src.core.config import get_settings
    from src.core.llm import LLMFactory

    settings = get_settings()
    llm = LLMFactory().get_llm()
    factory = AgentFactory(llm=llm, settings=settings)
    return factory.get_persona_agent(Role.CPO, state)


def _safe_cpo_run_impl(state: GlobalState) -> dict[str, Any]:
    """Wrapper for CPO execution with error handling."""
    cpo = _create_cpo_agent(state)
    result = cpo.run(state)
    if isinstance(result, dict):
        return result
    return {}


def safe_cpo_run(state: GlobalState) -> dict[str, Any]:
    return NodeExecutor.execute(_safe_cpo_run_impl, state, "Error in CPO Agent")


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


