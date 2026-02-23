import logging
from typing import Any

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.core.exceptions import V0GenerationError
from src.core.factory import AgentFactory
from src.core.nemawashi.engine import NemawashiEngine
from src.core.simulation import create_simulation_graph
from src.data.rag import RAG
from src.domain_models.mvp import MVP, Feature, MVPType, Priority
from src.domain_models.simulation import Role
from src.domain_models.state import GlobalState, Phase
from src.domain_models.validators import StateValidator

logger = logging.getLogger(__name__)


def safe_ideator_run(state: GlobalState) -> dict[str, Any]:
    """Wrapper for Ideator execution with error handling."""
    ideator = AgentFactory.get_ideator_agent()
    try:
        return ideator.run(state)
    except Exception:
        logger.exception("Error in Ideator Agent")
        return {}


def verification_node(state: GlobalState) -> dict[str, Any]:
    """
    Transition to Verification Phase.
    Here we prepare for the 'Mom Test' by setting the phase.
    The user will select the Riskiest Assumption (Gate 2) and provide transcripts.
    """
    try:
        StateValidator.validate_phase_requirements(state)
    except ValueError:
        logger.exception("Validation failed for Verification transition")
        return {}

    if not state.selected_idea:
        logger.error("Attempted to enter Verification Phase without a selected idea.")

    logger.info(f"Transitioning to Phase: {Phase.VERIFICATION}")
    return {"phase": Phase.VERIFICATION}


def transcript_ingestion_node(state: GlobalState) -> dict[str, Any]:
    """
    Ingest customer transcripts into the RAG system.
    Runs after Gate 2 (User Input of Transcript).
    """
    logger.info("Ingesting transcripts into RAG...")
    if not state.transcripts:
        logger.warning("No transcripts found in state to ingest.")
        return {}

    try:
        rag = RAG(persist_dir=state.rag_index_path)
        for transcript in state.transcripts:
            # We assume RAG handles duplicates or is stateless per run for now.
            # In a real system, we'd check existence.
            logger.info(f"Ingesting transcript from: {transcript.source}")
            rag.ingest_transcript(transcript)

        # Persist the index after ingestion
        rag.persist_index()

    except Exception:
        logger.exception("Error during transcript ingestion")
        # We don't halt, but CPO might have less data.

    return {}


def safe_simulation_run(state: GlobalState) -> dict[str, Any]:
    """
    Wrapper for Simulation execution with error handling.
    Runs the full turn-based simulation (Finance vs Sales vs New Employee).
    """
    logger.info("Starting Simulation Round (Turn-based Battle)")

    simulation_app = create_simulation_graph()
    try:
        final_state = simulation_app.invoke(state)
        if isinstance(final_state, dict):
            return {"debate_history": final_state.get("debate_history", [])}
        if hasattr(final_state, "debate_history"):
            return {"debate_history": final_state.debate_history}

        logger.warning("Simulation graph returned unknown state type.")
        return {}
    except Exception:
        logger.exception("Error in Simulation Graph")
        return {}


def nemawashi_analysis_node(state: GlobalState) -> dict[str, Any]:
    """
    Run Nemawashi (Consensus) analysis after the simulation.
    Updates the influence network with new opinion dynamics.
    """
    logger.info("Running Nemawashi Consensus Analysis...")

    if not state.influence_network:
        logger.warning("No influence network found. Skipping Nemawashi analysis.")
        return {}

    try:
        engine = NemawashiEngine()

        # Calculate new consensus (opinions)
        new_opinions = engine.calculate_consensus(state.influence_network)

        # Update the influence network in state
        # We create a deep copy to avoid mutation issues if any, but Pydantic handles it.
        # Actually, we can just update the stakeholders in place or create new list.
        updated_network = state.influence_network.model_copy(deep=True)

        for i, stakeholder in enumerate(updated_network.stakeholders):
            if i < len(new_opinions):
                stakeholder.initial_support = new_opinions[i]

        # Identify influencers (optional, for logging or CPO context)
        influencers = engine.identify_influencers(updated_network)
        logger.info(f"Identified Key Influencers: {influencers}")

        return {"influence_network": updated_network}

    except Exception:
        logger.exception("Error in Nemawashi Analysis")
        return {}


def safe_cpo_run(state: GlobalState) -> dict[str, Any]:
    """Wrapper for CPO execution with error handling."""
    cpo = AgentFactory.get_persona_agent(Role.CPO, state)
    try:
        return cpo.run(state)
    except Exception:
        logger.exception("Error in CPO Agent")
        return {}


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

    try:
        builder = AgentFactory.get_builder_agent()
        updates = builder.propose_features(state)
    except Exception:
        logger.exception("Error in Solution Proposal")
        return {"phase": Phase.SOLUTION}
    else:
        updates["phase"] = Phase.SOLUTION
        return updates


def mvp_generation_node(state: GlobalState) -> dict[str, Any]:
    """
    Generate MVP after user selection (Gate 3).
    """
    logger.info("Generating MVP (Cycle 5)...")

    try:
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

    except V0GenerationError:
        logger.exception("MVP Generation Failed")
        return {}
    except Exception:
        logger.exception("Error in MVP Generation")
        return {}


def pmf_node(state: GlobalState) -> dict[str, Any]:
    """Transition to PMF Phase."""
    try:
        StateValidator.validate_phase_requirements(state)
    except ValueError:
        logger.exception("Validation failed for PMF transition")
        return {}

    if not state.mvp_definition:
        logger.warning("Entering PMF Phase without an MVP definition.")

    logger.info(f"Transitioning to Phase: {Phase.PMF}")
    return {"phase": Phase.PMF}


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
    workflow.add_edge("pmf", END)

    # Compile with Interrupts for HITL Gates
    return workflow.compile(
        interrupt_after=[
            "ideator",
            "verification",
            "solution_proposal",
            "pmf"
        ]
    )
