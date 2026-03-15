import functools
import logging
from collections.abc import Callable
from typing import Any

from src.core.factory import AgentFactory
from src.core.nemawashi.engine import NemawashiEngine
from src.core.simulation import create_simulation_graph
from src.data.rag import RAG
from src.domain_models.simulation import Role
from src.domain_models.state import GlobalState, Phase
from src.domain_models.validators import StateValidator

logger = logging.getLogger(__name__)


def safe_node(
    error_msg: str = "Error in graph node",
) -> Callable[[Callable[..., Any]], Callable[..., dict[str, Any]]]:
    """Decorator to wrap graph nodes with consistent error handling."""

    def decorator(func: Callable[..., Any]) -> Callable[..., dict[str, Any]]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
            try:
                return func(*args, **kwargs)  # type: ignore[no-any-return]
            except Exception as e:
                logger.exception(error_msg, exc_info=True)
                return {"error": str(e)}

        return wrapper

    return decorator


@safe_node("Error in Ideator Agent")
def safe_ideator_run(state: GlobalState) -> dict[str, Any]:
    """Wrapper for Ideator execution with error handling."""
    ideator = AgentFactory.get_ideator_agent()
    return ideator.run(state)


@safe_node("Error in Verification Node")
def verification_node(state: GlobalState) -> dict[str, Any]:
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


@safe_node("Error during transcript ingestion")
def _ingest_impl(state: GlobalState) -> dict[str, Any]:
    rag = RAG(persist_dir=state.rag_index_path)

    # Process transcripts in chunks to manage memory
    chunk_size = 10
    total = len(state.transcripts)

    for i in range(0, total, chunk_size):
        chunk = state.transcripts[i : i + chunk_size]
        logger.info(f"Ingesting batch {i // chunk_size + 1}: {len(chunk)} transcripts")

        for transcript in chunk:
            rag.ingest_transcript(transcript)

        # Persist index after each chunk to free up ingestion buffers
        rag.persist_index()

    return {}


def transcript_ingestion_node(state: GlobalState) -> dict[str, Any]:
    """
    Ingest customer transcripts into the RAG system.
    Runs after Gate 2 (User Input of Transcript).
    """
    logger.info("Ingesting transcripts into RAG...")
    if not state.transcripts:
        logger.warning("No transcripts found in state to ingest.")
        return {}

    return _ingest_impl(state)


@safe_node("Error in Simulation Graph")
def safe_simulation_run(state: GlobalState) -> dict[str, Any]:
    """
    Wrapper for Simulation execution with error handling.
    Runs the full turn-based simulation (Finance vs Sales vs New Employee).
    """
    logger.info("Starting Simulation Round (Turn-based Battle)")

    simulation_app = create_simulation_graph()

    final_state = simulation_app.invoke(state)
    if isinstance(final_state, dict):
        return {"debate_history": final_state.get("debate_history", [])}
    if hasattr(final_state, "debate_history"):
        return {"debate_history": final_state.debate_history}

    logger.warning("Simulation graph returned unknown state type.")
    return {}


@safe_node("Error in Nemawashi Analysis")
def nemawashi_analysis_node(state: GlobalState) -> dict[str, Any]:
    """
    Run Nemawashi (Consensus) analysis after the simulation.
    Updates the influence network with new opinion dynamics.
    """
    logger.info("Running Nemawashi Consensus Analysis...")

    if not state.influence_network:
        logger.warning("No influence network found. Skipping Nemawashi analysis.")
        return {}

    engine = NemawashiEngine()

    # Calculate new consensus (opinions)
    new_opinions = engine.calculate_consensus(state.influence_network)

    # Update the influence network in state
    updated_network = state.influence_network.model_copy(deep=True)

    for i, stakeholder in enumerate(updated_network.stakeholders):
        if i < len(new_opinions):
            stakeholder.initial_support = new_opinions[i]

    # Identify influencers (optional, for logging or CPO context)
    influencers = engine.identify_influencers(updated_network)
    logger.info(f"Identified Key Influencers: {influencers}")

    return {"influence_network": updated_network}


@safe_node("Error in CPO Agent")
def safe_cpo_run(state: GlobalState) -> dict[str, Any]:
    """Wrapper for CPO execution with error handling."""
    cpo = AgentFactory.get_persona_agent(Role.CPO, state)
    return cpo.run(state)  # type: ignore


@safe_node("Error in Solution Proposal")
def _solution_proposal_impl(state: GlobalState) -> dict[str, Any]:
    return {"phase": Phase.SOLUTION}


def solution_proposal_node(state: GlobalState) -> dict[str, Any]:
    """
    Transition to Solution Phase and Propose Features.
    Prepares for Gate 3 (Problem-Solution Fit).
    """
    try:
        StateValidator.validate_phase_requirements(state)
    except ValueError:
        logger.exception("Validation failed for Solution transition")
        return {}

    if not state.target_persona:
        logger.warning("Entering Solution Phase without a defined target persona.")

    logger.info(f"Transitioning to Phase: {Phase.SOLUTION}")

    return _solution_proposal_impl(state)


@safe_node("Error in PMF Node")
@safe_node("Error in Spec Generation")
def spec_generation_node(state: GlobalState) -> dict[str, Any]:
    """
    Generate AgentPromptSpec and ExperimentPlan (Cycle 5).
    """
    logger.info("Generating Agent Prompt Spec and Experiment Plan (Cycle 5)...")

    builder = AgentFactory.get_builder_agent()
    result = builder.run(state)

    if not result:
        logger.error("BuilderAgent returned an empty result (possible validation failure).")
        return {"error": "Failed to generate specifications. Builder returned empty."}

    return result


@safe_node("Error in Experiment Planning")
def experiment_planning_node(state: GlobalState) -> dict[str, Any]:
    """
    Placeholder node if we want to split generation.
    Currently BuilderAgent handles both in spec_generation_node for atomicity.
    """
    logger.info("Experiment Planning Node: Passing through to PMF...")
    return {}


def pmf_node(state: GlobalState) -> dict[str, Any]:
    """Transition to PMF Phase."""
    StateValidator.validate_phase_requirements(state)

    if not state.agent_prompt_spec:
        logger.warning("Entering PMF Phase without an AgentPromptSpec.")

    logger.info(f"Transitioning to Phase: {Phase.PMF}")
    return {"phase": Phase.PMF}


@safe_node("Error in Governance Check")
def governance_node(state: GlobalState) -> dict[str, Any]:
    """
    Run Governance Agent for Cycle 6 (Ringi-sho).
    """
    logger.info("Running Governance Check...")

    agent = AgentFactory.get_governance_agent()
    updates = agent.run(state)

    updates["phase"] = Phase.GOVERNANCE
    return updates


@safe_node("Error in Final Artifact Generation")
def final_artifact_generation_node(state: GlobalState) -> dict[str, Any]:
    """
    Finalize artifacts by generating a comprehensive PDF of all Canvas and Models,
    and outputting the AgentPromptSpec and ExperimentPlan as Markdown files.
    """
    from pathlib import Path

    from src.core.config import get_settings
    from src.core.services.file_service import FileService

    logger.info("Generating Final Artifacts...")
    file_service = FileService()
    settings = get_settings()

    # Securely resolve output path, preventing path traversal
    # Ensure it's inside the current working directory
    base_dir = Path.cwd() / settings.file_service.output_directory
    base_dir.mkdir(parents=True, exist_ok=True)

    def write_markdown(filename: str, content: str) -> None:
        try:
            path = base_dir / filename
            file_service.save_text_async(content, str(path))
        except Exception:
            logger.exception(f"Failed to write markdown artifact: {filename}")

    try:
        # Write Markdown specs if they exist in state
        if state.agent_prompt_spec:
            content = f"# Agent Prompt Spec\n\n```json\n{state.agent_prompt_spec.model_dump_json(indent=2)}\n```"
            write_markdown("AgentPromptSpec.md", content)

        if state.experiment_plan:
            content = f"# Experiment Plan\n\n```json\n{state.experiment_plan.model_dump_json(indent=2)}\n```"
            write_markdown("ExperimentPlan.md", content)

        # Note: RingiSho is already saved by GovernanceAgent, but we'll export a duplicate
        # to the unified outputs directory for completeness.
        if state.ringi_sho:
            content = f"# Ringi-Sho\n\n```json\n{state.ringi_sho.model_dump_json(indent=2)}\n```"
            write_markdown("RingiSho.md", content)

        try:
            pdf_future = file_service.save_pdf_async(state, base_dir)
            pdf_future.result(timeout=30.0)  # Wait for PDF to finish with timeout
        except TimeoutError:
            logger.exception("PDF generation timed out after 30 seconds.")
        except Exception:
            logger.exception("PDF generation failed.")
    finally:
        # Ensure thread pool is shut down cleanly to prevent resource leaks
        file_service.shutdown()

    return {}
