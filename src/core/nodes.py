import logging
from collections.abc import Callable
from itertools import islice
from pathlib import Path
from typing import Any

from src.core.config import Settings
from src.core.factory import AgentFactory
from src.core.interfaces import IAgent, IOutputGenerationAgent, IRemasteredAgent
from src.core.nemawashi.engine import NemawashiEngine
from src.core.node_executor import NodeExecutor
from src.core.services.file_service import FileService
from src.core.services.pdf_generator import PDFGenerator
from src.core.simulation import create_simulation_graph
from src.core.utils import strip_html_tags
from src.core.workflow_builder import node_registry
from src.data.rag import RAG
from src.domain_models.simulation import Role
from src.domain_models.state import GlobalState, Phase
from src.domain_models.validators import StateValidator
from src.ui.renderer import ApprovalStampRenderer

logger = logging.getLogger(__name__)


# IDEATOR
def _ideator_run_impl(state: GlobalState, agent: IAgent) -> dict[str, Any]:
    res = agent.run(state)
    return res if isinstance(res, dict) else {}


def make_ideator_node(
    ideator_agent: IAgent, settings: Settings
) -> Callable[[GlobalState], dict[str, Any]]:
    executor = NodeExecutor(settings, agent=ideator_agent)
    return lambda state: executor.execute(_ideator_run_impl, state, "Error in Ideator Agent")


# VERIFICATION
def _verification_node_impl(state: GlobalState) -> dict[str, Any]:
    StateValidator.validate_phase_requirements(state)
    if not state.selected_idea:
        logger.error("Attempted to enter Verification Phase without a selected idea.")
    logger.info(f"Transitioning to Phase: {Phase.VERIFICATION}")
    return {"phase": Phase.VERIFICATION}


def verification_node(state: GlobalState) -> dict[str, Any]:
    # We create a dummy executor here since it takes no dependencies
    return NodeExecutor().execute(_verification_node_impl, state, "Error in Verification Node")


node_registry.register("verification")(verification_node)


# PERSONA
def _persona_node_impl(state: GlobalState, agent: IRemasteredAgent) -> dict[str, Any]:
    logger.info("Generating Persona...")
    res = agent.generate_persona(state)
    return res if isinstance(res, dict) else {}


def make_persona_node(
    agent: IRemasteredAgent, settings: Settings
) -> Callable[[GlobalState], dict[str, Any]]:
    executor = NodeExecutor(settings, agent=agent)
    return lambda state: executor.execute(_persona_node_impl, state, "Error in Persona Node")


# ALTERNATIVE ANALYSIS
def _alternative_analysis_node_impl(
    state: GlobalState, agent: IRemasteredAgent, settings: Settings
) -> dict[str, Any]:
    logger.info("Generating Alternative Analysis...")
    updates = agent.generate_alternative_analysis(state)
    if updates.get("alternative_analysis"):
        PDFGenerator.generate_canvas_pdf(
            updates["alternative_analysis"], "alternative_analysis.pdf", settings
        )
    return updates if isinstance(updates, dict) else {}


def make_alternative_analysis_node(
    agent: IRemasteredAgent, settings: Settings
) -> Callable[[GlobalState], dict[str, Any]]:
    executor = NodeExecutor(settings, agent=agent, settings_obj=settings)

    # the function definition needs settings_obj mapping
    def wrapper(
        state: GlobalState, agent: IRemasteredAgent, settings_obj: Settings
    ) -> dict[str, Any]:
        return _alternative_analysis_node_impl(state, agent, settings_obj)

    return lambda state: executor.execute(wrapper, state, "Error in Alternative Analysis Node")


# VPC
def _vpc_node_impl(
    state: GlobalState, agent: IRemasteredAgent, settings: Settings
) -> dict[str, Any]:
    logger.info("Generating Value Proposition Canvas...")
    updates = agent.generate_vpc(state)
    if updates.get("value_proposition"):
        PDFGenerator.generate_canvas_pdf(
            updates["value_proposition"], "value_proposition_canvas.pdf", settings
        )
        ApprovalStampRenderer("VPC Canvas", settings).start()
    return updates if isinstance(updates, dict) else {}


def make_vpc_node(
    agent: IRemasteredAgent, settings: Settings
) -> Callable[[GlobalState], dict[str, Any]]:
    executor = NodeExecutor(settings, agent=agent, settings_obj=settings)

    def wrapper(
        state: GlobalState, agent: IRemasteredAgent, settings_obj: Settings
    ) -> dict[str, Any]:
        return _vpc_node_impl(state, agent, settings_obj)

    return lambda state: executor.execute(wrapper, state, "Error in VPC Node")


# MENTAL MODEL JOURNEY
def _mental_model_journey_node_impl(
    state: GlobalState, agent: IRemasteredAgent, settings: Settings
) -> dict[str, Any]:
    logger.info("Generating Mental Model and Customer Journey...")
    updates = agent.generate_mental_model_and_journey(state)
    if updates.get("mental_model"):
        PDFGenerator.generate_canvas_pdf(
            updates["mental_model"], "mental_model_diagram.pdf", settings
        )
    if updates.get("customer_journey"):
        PDFGenerator.generate_canvas_pdf(
            updates["customer_journey"], "customer_journey.pdf", settings
        )

    if updates.get("mental_model") or updates.get("customer_journey"):
        ApprovalStampRenderer("Mental Model & Journey", settings).start()
    return updates if isinstance(updates, dict) else {}


def make_mental_model_journey_node(
    agent: IRemasteredAgent, settings: Settings
) -> Callable[[GlobalState], dict[str, Any]]:
    executor = NodeExecutor(settings, agent=agent, settings_obj=settings)

    def wrapper(
        state: GlobalState, agent: IRemasteredAgent, settings_obj: Settings
    ) -> dict[str, Any]:
        return _mental_model_journey_node_impl(state, agent, settings_obj)

    return lambda state: executor.execute(wrapper, state, "Error in Mental Model & Journey Node")


# SITEMAP WIREFRAME
def _sitemap_wireframe_node_impl(
    state: GlobalState, agent: IRemasteredAgent, settings: Settings
) -> dict[str, Any]:
    logger.info("Generating Sitemap and User Story...")
    updates = agent.generate_sitemap_and_wireframe(state)
    if updates.get("sitemap_and_story"):
        PDFGenerator.generate_canvas_pdf(
            updates["sitemap_and_story"], "sitemap_and_story.pdf", settings
        )
        ApprovalStampRenderer("Sitemap & Story", settings).start()
    return updates if isinstance(updates, dict) else {}


def make_sitemap_wireframe_node(
    agent: IRemasteredAgent, settings: Settings
) -> Callable[[GlobalState], dict[str, Any]]:
    executor = NodeExecutor(settings, agent=agent, settings_obj=settings)

    def wrapper(
        state: GlobalState, agent: IRemasteredAgent, settings_obj: Settings
    ) -> dict[str, Any]:
        return _sitemap_wireframe_node_impl(state, agent, settings_obj)

    return lambda state: executor.execute(wrapper, state, "Error in Sitemap & Wireframe Node")


# SPEC GENERATION
def _spec_generation_node_impl(
    state: GlobalState, agent: IOutputGenerationAgent, settings: Settings
) -> dict[str, Any]:
    logger.info("Generating Agent Prompt Spec...")
    updates = agent.generate_agent_prompt_spec(state)
    if updates.get("agent_prompt_spec"):
        output_dir = Path(settings.canvas_output_dir)
        if not output_dir.is_absolute():
            output_dir = Path.cwd() / output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        target_path = output_dir / "AgentPromptSpec.md"
        spec = updates["agent_prompt_spec"]

        safe_mermaid = strip_html_tags(spec.mermaid_flowchart)

        content = (
            f"# Agent Prompt Specification\n\n"
            f"## Core Story\n```json\n{spec.core_user_story.model_dump_json(indent=2)}\n```\n\n"
            f"## State Machine\n```json\n{spec.state_machine.model_dump_json(indent=2)}\n```\n\n"
            f"## State Machine (Mermaid)\n```mermaid\n{safe_mermaid}\n```\n"
        )

        file_service = FileService(settings=settings)
        file_service.save_text_async(content, target_path)

        ApprovalStampRenderer("Agent Prompt Spec", settings).start()
    return updates if isinstance(updates, dict) else {}


def make_spec_generation_node(
    agent: IOutputGenerationAgent, settings: Settings
) -> Callable[[GlobalState], dict[str, Any]]:
    executor = NodeExecutor(settings, agent=agent, settings_obj=settings)

    def wrapper(
        state: GlobalState, agent: IOutputGenerationAgent, settings_obj: Settings
    ) -> dict[str, Any]:
        return _spec_generation_node_impl(state, agent, settings_obj)

    return lambda state: executor.execute(wrapper, state, "Error in Spec Generation Node")


# EXPERIMENT PLANNING
def _experiment_planning_node_impl(
    state: GlobalState, agent: IOutputGenerationAgent, settings: Settings
) -> dict[str, Any]:
    logger.info("Generating Experiment Plan...")
    updates = agent.generate_experiment_plan(state)
    if updates.get("experiment_plan"):
        PDFGenerator.generate_canvas_pdf(
            updates["experiment_plan"], "experiment_plan.pdf", settings
        )

        output_dir = Path(settings.canvas_output_dir)
        if not output_dir.is_absolute():
            output_dir = Path.cwd() / output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        target_path = output_dir / "ExperimentPlan.md"

        content = f"# Experiment Plan\n\n```json\n{updates['experiment_plan'].model_dump_json(indent=2)}\n```\n"

        file_service = FileService(settings=settings)
        file_service.save_text_async(content, target_path)

        ApprovalStampRenderer("Experiment Plan", settings).start()
    return updates if isinstance(updates, dict) else {}


def make_experiment_planning_node(
    agent: IOutputGenerationAgent, settings: Settings
) -> Callable[[GlobalState], dict[str, Any]]:
    executor = NodeExecutor(settings, agent=agent, settings_obj=settings)

    def wrapper(
        state: GlobalState, agent: IOutputGenerationAgent, settings_obj: Settings
    ) -> dict[str, Any]:
        return _experiment_planning_node_impl(state, agent, settings_obj)

    return lambda state: executor.execute(wrapper, state, "Error in Experiment Planning Node")


# VIRTUAL CUSTOMER
def _virtual_customer_node_impl(state: GlobalState, agent: IAgent) -> dict[str, Any]:
    logger.info("Running Virtual Customer Simulation...")
    res = agent.run(state)
    return res if isinstance(res, dict) else {}


def make_virtual_customer_node(
    agent: IAgent, settings: Settings
) -> Callable[[GlobalState], dict[str, Any]]:
    executor = NodeExecutor(settings, agent=agent)
    return lambda state: executor.execute(
        _virtual_customer_node_impl, state, "Error in Virtual Customer Node"
    )


# 3H REVIEW
def _review_3h_node_impl(
    state: GlobalState, hacker_agent: IAgent, hipster_agent: IAgent, hustler_agent: IAgent
) -> dict[str, Any]:
    logger.info("Running 3H Review...")
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


def make_review_3h_node(
    hacker_agent: IAgent, hipster_agent: IAgent, hustler_agent: IAgent, settings: Settings
) -> Callable[[GlobalState], dict[str, Any]]:
    executor = NodeExecutor(
        settings,
        hacker_agent=hacker_agent,
        hipster_agent=hipster_agent,
        hustler_agent=hustler_agent,
    )
    return lambda state: executor.execute(_review_3h_node_impl, state, "Error in 3H Review Node")


# TRANSCRIPT INGESTION
def _validate_transcripts(state: GlobalState) -> None:
    if not state.transcripts:
        msg = "No transcripts found in state to ingest. Missing validation."
        raise ValueError(msg)


def _ingest_impl(state: GlobalState, settings: Settings) -> dict[str, Any]:
    rag = RAG(settings=settings, persist_dir=state.rag_index_path)
    max_transcripts = settings.rag.max_transcripts
    chunk_size = settings.rag.batch_size
    transcript_iter = iter(state.transcripts)
    processed_count = 0
    try:
        while processed_count < max_transcripts:
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
        msg = f"RAG ingestion failed: {e}"
        raise ValueError(msg) from e
    return {}


def _transcript_ingestion_node_impl(state: GlobalState, settings: Settings) -> dict[str, Any]:
    logger.info("Ingesting transcripts into RAG...")
    _validate_transcripts(state)
    return _ingest_impl(state, settings)


def make_transcript_ingestion_node(settings: Settings) -> Callable[[GlobalState], dict[str, Any]]:
    executor = NodeExecutor(settings, settings_obj=settings)

    def wrapper(state: GlobalState, settings_obj: Settings) -> dict[str, Any]:
        return _transcript_ingestion_node_impl(state, settings_obj)

    return lambda state: executor.execute(wrapper, state, "Error during transcript ingestion")


# SIMULATION
def _transform_simulation_state(final_state: Any) -> dict[str, Any]:
    if isinstance(final_state, dict):
        return {"debate_history": final_state.get("debate_history", [])}
    if hasattr(final_state, "debate_history"):
        return {"debate_history": final_state.debate_history}
    logger.warning("Simulation graph returned unknown state type.")
    return {}


def _safe_simulation_run_impl(
    state: GlobalState, settings: Settings, factory: AgentFactory
) -> dict[str, Any]:
    logger.info("Starting Simulation Round (Turn-based Battle)")
    simulation_app = create_simulation_graph(settings, factory)
    final_state = simulation_app.invoke(state)
    return _transform_simulation_state(final_state)


def make_safe_simulation_run_node(
    settings: Settings, factory: AgentFactory
) -> Callable[[GlobalState], dict[str, Any]]:
    executor = NodeExecutor(settings, settings_obj=settings, factory=factory)

    def wrapper(
        state: GlobalState, settings_obj: Settings, factory: AgentFactory
    ) -> dict[str, Any]:
        return _safe_simulation_run_impl(state, settings_obj, factory)

    return lambda state: executor.execute(wrapper, state, "Error in Simulation Graph")


# NEMAWASHI ANALYSIS
def _identify_and_log_influencers(engine: NemawashiEngine, network: Any) -> None:
    influencers = engine.identify_influencers(network)
    logger.info(f"Identified Key Influencers: {influencers}")


def _nemawashi_analysis_node_impl(
    state: GlobalState, engine_factory: Callable[[], NemawashiEngine]
) -> dict[str, Any]:
    logger.info("Running Nemawashi Consensus Analysis...")
    if not state.influence_network:
        logger.warning("No influence network found. Skipping Nemawashi analysis.")
        return {}
    engine = engine_factory()
    new_opinions = engine.calculate_consensus(state.influence_network)
    updated_network = state.influence_network.model_copy(deep=True)
    for i, stakeholder in enumerate(updated_network.stakeholders):
        if i < len(new_opinions):
            stakeholder.initial_support = new_opinions[i]
    _identify_and_log_influencers(engine, updated_network)
    return {"influence_network": updated_network}


def make_nemawashi_analysis_node(
    engine_factory: Callable[[], NemawashiEngine], settings: Settings
) -> Callable[[GlobalState], dict[str, Any]]:
    executor = NodeExecutor(settings, engine_factory=engine_factory)
    return lambda state: executor.execute(
        _nemawashi_analysis_node_impl, state, "Error in Nemawashi Analysis"
    )


# CPO AGENT
def _create_cpo_agent(state: GlobalState, settings: Settings, llm: Any) -> Any:
    factory = AgentFactory(llm=llm, settings=settings)
    return factory.get_persona_agent(Role.CPO, state)


def _safe_cpo_run_impl(state: GlobalState, settings: Settings, llm: Any) -> dict[str, Any]:
    cpo = _create_cpo_agent(state, settings, llm)
    result = cpo.run(state)
    if isinstance(result, dict):
        return result
    return {}


def make_safe_cpo_run_node(settings: Settings, llm: Any) -> Callable[[GlobalState], dict[str, Any]]:
    executor = NodeExecutor(settings, settings_obj=settings, llm=llm)

    def wrapper(state: GlobalState, settings_obj: Settings, llm: Any) -> dict[str, Any]:
        return _safe_cpo_run_impl(state, settings_obj, llm)

    return lambda state: executor.execute(wrapper, state, "Error in CPO Agent")


# GOVERNANCE
def _transition_phase(updates: dict[str, Any], phase: Phase) -> dict[str, Any]:
    updates["phase"] = phase
    return updates


def _governance_node_impl(state: GlobalState, agent: IAgent) -> dict[str, Any]:
    logger.info("Running Governance Check...")
    updates = agent.run(state)
    return _transition_phase(updates, Phase.GOVERNANCE)


def make_governance_node(
    agent: IAgent, settings: Settings
) -> Callable[[GlobalState], dict[str, Any]]:
    executor = NodeExecutor(settings, agent=agent)
    return lambda state: executor.execute(_governance_node_impl, state, "Error in Governance Check")
