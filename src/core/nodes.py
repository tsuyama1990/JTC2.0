import functools
import logging
from collections.abc import Callable
from typing import Any

from src.core.factory import AgentFactory
from src.core.nemawashi.engine import NemawashiEngine
from src.core.services.pdf_generator import PDFGenerator
from src.core.simulation import create_simulation_graph
from src.data.rag import RAG
from src.domain_models.mvp import MVP, Feature, MVPType, Priority
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


@safe_node("Error in Persona Node")
def persona_node(state: GlobalState) -> dict[str, Any]:
    """Phase 2: Generate Persona."""
    logger.info("Generating Persona...")
    agent = AgentFactory.get_remastered_agent()
    return agent.generate_persona(state)

@safe_node("Error in Alternative Analysis Node")
def alternative_analysis_node(state: GlobalState) -> dict[str, Any]:
    """Phase 2: Generate Alternative Analysis."""
    logger.info("Generating Alternative Analysis...")
    agent = AgentFactory.get_remastered_agent()
    updates = agent.generate_alternative_analysis(state)
    if updates.get("alternative_analysis"):
        PDFGenerator.generate_canvas_pdf(updates["alternative_analysis"], "alternative_analysis.pdf")
    return updates

@safe_node("Error in VPC Node")
def vpc_node(state: GlobalState) -> dict[str, Any]:
    """Phase 2: Generate Value Proposition Canvas."""
    logger.info("Generating Value Proposition Canvas...")
    agent = AgentFactory.get_remastered_agent()
    updates = agent.generate_vpc(state)
    if updates.get("value_proposition"):
        PDFGenerator.generate_canvas_pdf(updates["value_proposition"], "value_proposition_canvas.pdf")
    return updates

@safe_node("Error in Mental Model & Journey Node")
def mental_model_journey_node(state: GlobalState) -> dict[str, Any]:
    """Phase 3: Generate Mental Model & Customer Journey."""
    logger.info("Generating Mental Model and Customer Journey...")
    agent = AgentFactory.get_remastered_agent()
    updates = agent.generate_mental_model_and_journey(state)
    if updates.get("mental_model"):
        PDFGenerator.generate_canvas_pdf(updates["mental_model"], "mental_model_diagram.pdf")
    if updates.get("customer_journey"):
        PDFGenerator.generate_canvas_pdf(updates["customer_journey"], "customer_journey.pdf")
    return updates

@safe_node("Error in Sitemap & Wireframe Node")
def sitemap_wireframe_node(state: GlobalState) -> dict[str, Any]:
    """Phase 3: Generate Sitemap and Wireframe (User Story)."""
    logger.info("Generating Sitemap and User Story...")
    agent = AgentFactory.get_remastered_agent()
    updates = agent.generate_sitemap_and_wireframe(state)
    if updates.get("sitemap_and_story"):
        PDFGenerator.generate_canvas_pdf(updates["sitemap_and_story"], "sitemap_and_story.pdf")
    return updates

@safe_node("Error in Spec Generation Node")
def spec_generation_node(state: GlobalState) -> dict[str, Any]:
    """Phase 5: Generate Agent Prompt Spec."""
    logger.info("Generating Agent Prompt Spec...")
    agent = AgentFactory.get_output_generation_agent()
    updates = agent.generate_agent_prompt_spec(state)
    if updates.get("agent_prompt_spec"):
        from pathlib import Path

        from src.core.config import get_settings
        settings = get_settings()
        output_dir = Path(settings.canvas_output_dir)
        if not output_dir.is_absolute():
            output_dir = Path.cwd() / output_dir
        output_dir.mkdir(parents=True, exist_ok=True)
        with (output_dir / "AgentPromptSpec.md").open("w") as f:
            f.write(f"# Agent Prompt Specification\n\n```json\n{updates['agent_prompt_spec'].model_dump_json(indent=2)}\n```\n")
    return updates

@safe_node("Error in Experiment Planning Node")
def experiment_planning_node(state: GlobalState) -> dict[str, Any]:
    """Phase 6: Generate Experiment Plan."""
    logger.info("Generating Experiment Plan...")
    agent = AgentFactory.get_output_generation_agent()
    updates = agent.generate_experiment_plan(state)
    if updates.get("experiment_plan"):
        PDFGenerator.generate_canvas_pdf(updates["experiment_plan"], "experiment_plan.pdf")
    return updates

@safe_node("Error in Virtual Customer Node")
def virtual_customer_node(state: GlobalState) -> dict[str, Any]:
    """Phase 4: Virtual Customer Interview."""
    logger.info("Running Virtual Customer Simulation...")
    agent = AgentFactory.get_virtual_customer_agent()
    return agent.run(state)

@safe_node("Error in 3H Review Node")
def review_3h_node(state: GlobalState) -> dict[str, Any]:
    """Phase 4: 3H Review (Hacker, Hipster, Hustler)."""
    logger.info("Running 3H Review...")
    hacker = AgentFactory.get_hacker_agent()
    hipster = AgentFactory.get_hipster_agent()
    hustler = AgentFactory.get_hustler_agent()

    # Run sequentially and accumulate messages
    state_updates: dict[str, Any] = {"debate_history": list(state.debate_history)}
    for agent in [hacker, hipster, hustler]:
        updates = agent.run(state)
        if "debate_history" in updates:
            state_updates["debate_history"].extend(
                [msg for msg in updates["debate_history"] if msg not in state_updates["debate_history"]]
            )
            state.debate_history = state_updates["debate_history"]

    return state_updates



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


@safe_node("Error during transcript ingestion")
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


@safe_node("Error in Solution Proposal Node")
def solution_proposal_node(state: GlobalState) -> dict[str, Any]:
    """
    Transition to Solution Phase and Propose Features.
    Prepares for Gate 3 (Problem-Solution Fit).
    """
    StateValidator.validate_phase_requirements(state)

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
            v0_url=updates.get("mvp_url"),  # Map URL if present
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
