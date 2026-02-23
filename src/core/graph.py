from typing import Any

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.agents.ideator import IdeatorAgent
from src.agents.personas import CPOAgent, NewEmployeeAgent
from src.core.llm import get_llm
from src.domain_models.state import GlobalState, Phase


def create_app() -> CompiledStateGraph:  # type: ignore[type-arg]
    """Create and compile the LangGraph application."""
    llm = get_llm()
    ideator = IdeatorAgent(llm)
    cpo = CPOAgent(llm)
    new_employee = NewEmployeeAgent(llm)

    workflow = StateGraph(GlobalState)

    # Add Nodes
    workflow.add_node("ideator", ideator.run)

    # Placeholder for Verification Phase (Gate 2)
    def verification_node(state: GlobalState) -> dict[str, Any]:
        return {"phase": Phase.VERIFICATION}

    workflow.add_node("verification", verification_node)

    # Placeholder for Solution Phase (Gate 3)
    def solution_node(state: GlobalState) -> dict[str, Any]:
        return {"phase": Phase.SOLUTION}

    workflow.add_node("solution", solution_node)

    # Placeholder for PMF Phase (Gate 4)
    def pmf_node(state: GlobalState) -> dict[str, Any]:
        return {"phase": Phase.PMF}

    workflow.add_node("pmf", pmf_node)

    # Simulation Nodes (simplified loop)
    # In a real run, this would cycle between Finance, Sales, and New Employee
    # For now, we just invoke New Employee and then CPO
    workflow.add_node("simulation_round", new_employee.run)
    workflow.add_node("cpo_mentoring", cpo.run)

    # Edges
    workflow.set_entry_point("ideator")

    # After Ideator -> User selection (HITL) -> Verification
    workflow.add_edge("ideator", "verification")

    # After Verification -> Simulation Loop
    workflow.add_edge("verification", "simulation_round")

    # After Simulation Round -> CPO Mentoring
    workflow.add_edge("simulation_round", "cpo_mentoring")

    # After CPO -> Solution (Simplified for now)
    workflow.add_edge("cpo_mentoring", "solution")

    # After Solution -> PMF
    workflow.add_edge("solution", "pmf")

    workflow.add_edge("pmf", END)

    # Interrupts (HITL Gates)
    # We interrupt AFTER each major phase to allow user intervention (Gates 1-4)
    return workflow.compile(
        interrupt_after=["ideator", "verification", "solution", "pmf"]
    )
