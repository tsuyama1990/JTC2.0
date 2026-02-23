import logging
from typing import Any

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.core.factory import AgentFactory
from src.core.simulation import create_simulation_graph
from src.domain_models.simulation import Role
from src.domain_models.state import GlobalState, GlobalStateValidators, Phase

logger = logging.getLogger(__name__)


def safe_ideator_run(state: GlobalState) -> dict[str, Any]:
    """Wrapper for Ideator execution with error handling."""
    ideator = AgentFactory.get_ideator_agent()
    try:
        return ideator.run(state)
    except Exception as e:
        logger.error(f"Error in Ideator Agent: {e}", exc_info=True)
        return {}


def verification_node(state: GlobalState) -> dict[str, Any]:
    """Transition to Verification Phase."""
    # Explicit validation before transition
    try:
        GlobalStateValidators.validate_phase_requirements(state)
    except ValueError as e:
        logger.error(f"Validation failed for Verification transition: {e}")
        return {} # Or handle error state

    if not state.selected_idea:
        logger.error("Attempted to enter Verification Phase without a selected idea.")

    logger.info(f"Transitioning to Phase: {Phase.VERIFICATION}")
    return {"phase": Phase.VERIFICATION}


def safe_simulation_run(state: GlobalState) -> dict[str, Any]:
    """
    Wrapper for Simulation execution with error handling.

    Runs the full turn-based simulation (Finance vs Sales vs New Employee).
    """
    logger.info("Starting Simulation Round (Turn-based Battle)")

    # We could cache the compiled graph here if needed, but it's lightweight to create
    # given the lazy agent instantiation pattern.
    simulation_app = create_simulation_graph()
    try:
        # invoke returns the final state dict/object
        final_state = simulation_app.invoke(state)
        # Extract the updated debate history
        # Depending on invoke return type (dict if input was dict, likely dict)
        if isinstance(final_state, dict):
            return {"debate_history": final_state.get("debate_history", [])}
        # If it returns GlobalState object
        if hasattr(final_state, "debate_history"):
            return {"debate_history": final_state.debate_history}

        logger.warning("Simulation graph returned unknown state type.")
        return {}
    except Exception as e:
        logger.error(f"Error in Simulation Graph: {e}", exc_info=True)
        return {}


def safe_cpo_run(state: GlobalState) -> dict[str, Any]:
    """Wrapper for CPO execution with error handling."""
    cpo = AgentFactory.get_persona_agent(Role.CPO, state)
    try:
        res: dict[str, Any] = cpo.run(state)
    except Exception as e:
        logger.error(f"Error in CPO Agent: {e}", exc_info=True)
        return {}
    else:
        return res


def solution_node(state: GlobalState) -> dict[str, Any]:
    """Transition to Solution Phase."""
    try:
        GlobalStateValidators.validate_phase_requirements(state)
    except ValueError as e:
        logger.error(f"Validation failed for Solution transition: {e}")
        # In a real app we might route to an error node or retry.
        # For now, we log and proceed (or stay in current phase implicitly if we return empty?)
        # Returning empty means no state update, effectively halting or looping.
        return {}

    if not state.target_persona:
        logger.warning("Entering Solution Phase without a defined target persona.")

    logger.info(f"Transitioning to Phase: {Phase.SOLUTION}")
    return {"phase": Phase.SOLUTION}


def pmf_node(state: GlobalState) -> dict[str, Any]:
    """Transition to PMF Phase."""
    try:
        GlobalStateValidators.validate_phase_requirements(state)
    except ValueError as e:
        logger.error(f"Validation failed for PMF transition: {e}")
        return {}

    if not state.mvp_definition:
        logger.warning("Entering PMF Phase without an MVP definition.")

    logger.info(f"Transitioning to Phase: {Phase.PMF}")
    return {"phase": Phase.PMF}


def create_app() -> CompiledStateGraph:  # type: ignore[type-arg]
    """
    Create and compile the LangGraph application.

    This graph implements the "The JTC 2.0" architecture with 4 critical Decision Gates
    (Human-in-the-Loop) and a Simulation Loop.

    Nodes:
    - ideator: Generates ideas (Phase: Ideation). Interrupts after for User Selection (Gate 1).
    - verification: Validates selection and prepares for Verification. Interrupts after for User Assumption Selection (Gate 2).
    - simulation_round: Runs the debate simulation (Finance, Sales, New Employee).
    - cpo_mentoring: CPO provides advice based on debate.
    - solution: Defines MVP. Interrupts after for Feature Selection (Gate 3).
    - pmf: Checks Product-Market Fit. Interrupts after for Pivot Decision (Gate 4).

    Returns:
        CompiledStateGraph: The compiled LangGraph application.
    """
    workflow = StateGraph(GlobalState)

    # --- NODE DEFINITIONS ---
    workflow.add_node("ideator", safe_ideator_run)
    workflow.add_node("verification", verification_node)
    workflow.add_node("simulation_round", safe_simulation_run)
    workflow.add_node("cpo_mentoring", safe_cpo_run)
    workflow.add_node("solution", solution_node)
    workflow.add_node("pmf", pmf_node)

    # --- EDGE DEFINITIONS ---
    workflow.set_entry_point("ideator")

    # Gate 1: Idea Verification (Plan A Selection)
    workflow.add_edge("ideator", "verification")

    # Gate 2: Customer-Problem Fit (Riskiest Assumption)
    workflow.add_edge("verification", "simulation_round")

    # Simulation Logic
    workflow.add_edge("simulation_round", "cpo_mentoring")

    # Gate 3: Problem-Solution Fit (MVP Scope)
    workflow.add_edge("cpo_mentoring", "solution")
    workflow.add_edge("solution", "pmf")

    # Gate 4: Product-Market Fit (Pivot Decision)
    workflow.add_edge("pmf", END)

    # Compile with Interrupts for HITL Gates
    return workflow.compile(interrupt_after=["ideator", "verification", "solution", "pmf"])
