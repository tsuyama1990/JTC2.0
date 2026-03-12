import functools
import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from src.core.factory import AgentFactory
from src.core.nemawashi.engine import NemawashiEngine
from src.core.simulation import create_simulation_graph
from src.data.rag import RAG
from src.domain_models.simulation import Role
from src.domain_models.state import GlobalState, Phase
from src.domain_models.validators import StateValidator

logger = logging.getLogger(__name__)

T = TypeVar("T")


def safe_node(
    error_msg: str = "Error in graph node",
) -> Callable[[Callable[..., dict[str, Any]]], Callable[..., dict[str, Any]]]:
    """Decorator to wrap graph nodes with consistent error handling."""

    def decorator(func: Callable[..., dict[str, Any]]) -> Callable[..., dict[str, Any]]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:
            try:
                return func(*args, **kwargs)
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
    """
    StateValidator.validate_phase_requirements(state)

    if not state.selected_idea:
        logger.error("Attempted to enter Verification Phase without a selected idea.")

    logger.info(f"Transitioning to Phase: {Phase.CPF}")
    return {"phase": Phase.CPF}


@safe_node("Error in Persona Generation Node")
def persona_node(state: GlobalState) -> dict[str, Any]:
    """Generate target persona and empathy map."""
    logger.info("Generating Persona and Empathy Map...")
    agent = AgentFactory.get_persona_generator_agent()
    return agent.run(state)


@safe_node("Error in Alternative Analysis Node")
def alternative_analysis_node(state: GlobalState) -> dict[str, Any]:
    """Generate Alternative Analysis."""
    logger.info("Generating Alternative Analysis...")
    agent = AgentFactory.get_alternative_analysis_agent()
    return agent.run(state)


@safe_node("Error in Value Proposition Node")
def vpc_node(state: GlobalState) -> dict[str, Any]:
    """Generate Value Proposition Canvas."""
    logger.info("Generating Value Proposition Canvas...")
    agent = AgentFactory.get_vpc_agent()
    result = agent.run(state)

    # Generate PDF at HITL Gate 1.5 if generation is successful
    if "value_proposition_canvas" in result and state.target_persona and state.alternative_analysis:
        from src.core.config import get_settings
        from src.core.services.file_service import FileService

        settings = get_settings()
        file_service = FileService()

        try:
            # Output directory for the PDF from settings
            output_dir = Path.cwd() / settings.canvas_output_dir
            file_service.generate_vpc_pdf(
                persona=state.target_persona,
                analysis=state.alternative_analysis,
                vpc=result["value_proposition_canvas"],
                output_dir=output_dir,
            )
        except Exception:
            logger.exception("Failed to generate PDF at HITL Gate 1.5")

    return result


@safe_node("Error during transcript ingestion")
def _ingest_impl(state: GlobalState) -> dict[str, Any]:
    rag = RAG(persist_dir=state.rag_index_path)

    # Process transcripts in chunks to manage memory
    from src.core.config import get_settings

    settings = get_settings()
    chunk_size = settings.rag_batch_size
    total = len(state.transcripts)

    import os
    from concurrent.futures import ThreadPoolExecutor, as_completed

    max_workers = (os.cpu_count() or 1) * 2 + 1

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for i in range(0, total, chunk_size):
            chunk = state.transcripts[i : i + chunk_size]
            logger.info(f"Submitting batch {i // chunk_size + 1}: {len(chunk)} transcripts")
            # Submit chunk to executor
            for transcript in chunk:
                futures.append(executor.submit(rag.ingest_transcript, transcript))

        # Wait for all ingestion tasks to complete
        for i, future in enumerate(as_completed(futures)):
            try:
                future.result()
                if (i + 1) % 10 == 0:
                    logger.info(f"Completed ingestion of {i + 1}/{total} transcripts")
            except Exception:
                logger.exception("Failed to ingest a transcript")

    # Persist index once after all chunks to avoid O(n) I/O bottleneck
    rag.persist_index()

    return {}


@safe_node("Error in Transcript Ingestion")
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


@safe_node("Error in Mental Model & Journey Mapping")
def mental_model_journey_node(state: GlobalState) -> dict[str, Any]:
    """Generate Mental Model and Customer Journey."""
    logger.info("Generating Mental Model and Customer Journey...")
    agent = AgentFactory.get_mental_model_journey_agent()
    updates = agent.run(state)
    updates["phase"] = Phase.PSF
    return updates


@safe_node("Error in Sitemap & Wireframing")
def sitemap_wireframe_node(state: GlobalState) -> dict[str, Any]:
    """Generate Sitemap and Wireframe (Story)."""
    logger.info("Generating Sitemap and Lo-Fi Wireframing...")
    agent = AgentFactory.get_sitemap_wireframe_agent()
    return agent.run(state)


@safe_node("Error in Virtual Customer Interview")
def virtual_customer_node(state: GlobalState) -> dict[str, Any]:
    """Run Virtual Customer Interview."""
    logger.info("Running Virtual Solution Interview...")
    agent = AgentFactory.get_virtual_customer_agent()
    updates = agent.run(state)
    updates["phase"] = Phase.VALIDATION
    return updates


@safe_node("Error in 3H Review")
def th_review_node(state: GlobalState) -> dict[str, Any]:
    """Run 3H Review (Hacker, Hipster, Hustler)."""
    logger.info("Running 3H Review...")
    agent = AgentFactory.get_3h_review_agent()
    return agent.run(state)


@safe_node("Error in Spec Generation")
def spec_generation_node(state: GlobalState) -> dict[str, Any]:
    """Generate Agent Prompt Spec."""
    logger.info("Generating Agent Prompt Spec...")
    builder = AgentFactory.get_builder_agent()
    updates = builder.generate_spec(state)
    updates["phase"] = Phase.OUTPUT
    return updates


@safe_node("Error in Experiment Planning")
def experiment_planning_node(state: GlobalState) -> dict[str, Any]:
    """Generate Experiment Plan."""
    logger.info("Generating Experiment Plan...")
    builder = AgentFactory.get_builder_agent()
    updates = builder.generate_experiment_plan(state)

    if "experiment_plan" in updates and state.sitemap_and_story:
        plan = updates["experiment_plan"]
        from src.domain_models.mvp import MVP, Feature, MVPType, Priority

        # Determine the core feature from the generated user story and experiment plan
        feature_name = state.sitemap_and_story.core_story.i_want_to
        feature_name = feature_name if len(feature_name) <= 50 else feature_name[:47] + "..."
        feature_name = feature_name if len(feature_name) >= 3 else feature_name + " feature"

        description = plan.riskiest_assumption
        from src.core.config import get_settings

        min_len = get_settings().validation.min_content_length
        if len(description) < min_len:
            description = description.ljust(min_len, ".")

        mvp = MVP(
            type=MVPType.SINGLE_FEATURE,
            core_features=[
                Feature(
                    name=feature_name,
                    description=description,
                    priority=Priority.MUST_HAVE,
                )
            ],
            success_criteria=plan.pivot_condition,
        )
        updates["mvp_definition"] = mvp

    return updates


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
