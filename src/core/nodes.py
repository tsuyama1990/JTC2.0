import functools
import logging
from collections.abc import Callable
from typing import Any

from src.core.factory import AgentFactory
from src.core.nemawashi.engine import NemawashiEngine
from src.core.simulation import create_simulation_graph
from src.data.rag import RAG
from src.domain_models.mvp import MVP, Feature, MVPType, Priority
from src.domain_models.simulation import Role
from src.domain_models.state import GlobalState, Phase
from src.domain_models.validators import StateValidator

logger = logging.getLogger(__name__)


def safe_node(error_msg: str = "Error in graph node") -> Callable[..., dict[str, Any]]:
    """Decorator to wrap graph nodes with consistent error handling."""
    def decorator(func: Callable[..., Any]) -> Callable[..., dict[str, Any]]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
            try:
                return func(*args, **kwargs)  # type: ignore[no-any-return]
            except Exception:
                logger.exception(error_msg)
                return {}
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
    return cpo.run(state)


@safe_node("Error in Solution Proposal")
def _solution_proposal_impl(state: GlobalState) -> dict[str, Any]:
    builder = AgentFactory.get_builder_agent()
    updates = builder.propose_features(state)
    updates["phase"] = Phase.SOLUTION
    return updates


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


@safe_node("Error in MVP Generation")
def mvp_generation_node(state: GlobalState) -> dict[str, Any]:
    """
    Generate MVP after user selection (Gate 3).
    """
    logger.info("Generating MVP (Cycle 5)...")

    builder = AgentFactory.get_builder_agent()
    updates = builder.generate_mvp(state)

    # If MVP Spec is generated, ensure MVP Definition exists for validation
    if updates.get("mvp_spec"):
        spec = updates["mvp_spec"]
        mvp = MVP(
            type=MVPType.SINGLE_FEATURE,
            core_features=[
                Feature(
                    name=spec.core_feature,
                    description=f"Core feature: {spec.core_feature}",
                    priority=Priority.MUST_HAVE,
                )
            ],
            success_criteria="User engagement and feedback.",
            v0_url=updates.get("mvp_url") # Map URL if present
        )
        updates["mvp_definition"] = mvp

    return updates


@safe_node("Error in PMF Node")
def pmf_node(state: GlobalState) -> dict[str, Any]:
    """Transition to PMF Phase."""
    StateValidator.validate_phase_requirements(state)

    if not state.mvp_definition:
        logger.warning("Entering PMF Phase without an MVP definition.")

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
