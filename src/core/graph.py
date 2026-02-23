from typing import Any

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.agents.ideator import IdeatorAgent
from src.agents.personas import CPOAgent, NewEmployeeAgent
from src.core.llm import get_llm
from src.domain_models.state import GlobalState, Phase


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
    llm = get_llm()
    ideator = IdeatorAgent(llm)
    cpo = CPOAgent(llm)
    new_employee = NewEmployeeAgent(llm)

    workflow = StateGraph(GlobalState)

    # --- NODE DEFINITIONS ---

    # 1. Ideation Node
    workflow.add_node("ideator", ideator.run)

    # 2. Verification Node (Gate 2 Preparation)
    def verification_node(state: GlobalState) -> dict[str, Any]:
        """
        Transition to Verification Phase.
        In a full implementation, this would involve generating the Persona
        based on the selected idea before asking the user for the 'Riskiest Assumption'.
        """
        if not state.selected_idea:
            # In a real app, we might handle this error or loop back
            pass
        return {"phase": Phase.VERIFICATION}

    workflow.add_node("verification", verification_node)

    # 3. Simulation Loop Nodes
    # Ideally, this loop cycles between Finance -> Sales -> New Employee -> CPO
    workflow.add_node("simulation_round", new_employee.run)
    workflow.add_node("cpo_mentoring", cpo.run)

    # 4. Solution Node (Gate 3 Preparation)
    def solution_node(state: GlobalState) -> dict[str, Any]:
        """
        Transition to Solution Phase.
        Prepares the MVP definition based on the simulation outcome.
        User will then select 'Must-have' features.
        """
        if not state.target_persona:
             # Logic to ensure persona exists would go here
             pass
        return {"phase": Phase.SOLUTION}

    workflow.add_node("solution", solution_node)

    # 5. PMF Node (Gate 4 Preparation)
    def pmf_node(state: GlobalState) -> dict[str, Any]:
        """
        Transition to PMF Phase.
        Analyzes MVP results and prepares AARRR metrics.
        User will then decide to Pivot or Persevere.
        """
        if not state.mvp_definition:
             pass
        return {"phase": Phase.PMF}

    workflow.add_node("pmf", pmf_node)

    # --- EDGE DEFINITIONS ---

    workflow.set_entry_point("ideator")

    # Gate 1: Idea Verification (Plan A Selection)
    # The graph interrupts AFTER 'ideator'. User selects idea externally.
    # Then we proceed to 'verification'.
    workflow.add_edge("ideator", "verification")

    # Gate 2: Customer-Problem Fit (Riskiest Assumption)
    # The graph interrupts AFTER 'verification'. User selects assumption/persona details.
    # Then we proceed to the simulation.
    workflow.add_edge("verification", "simulation_round")

    # Simulation Logic
    workflow.add_edge("simulation_round", "cpo_mentoring")

    # In this simplified flow, we go from CPO directly to Solution.
    # A full loop would verify if 'approval' is granted.
    workflow.add_edge("cpo_mentoring", "solution")

    # Gate 3: Problem-Solution Fit (MVP Scope)
    # Interrupts AFTER 'solution'. User selects features.
    workflow.add_edge("solution", "pmf")

    # Gate 4: Product-Market Fit (Pivot Decision)
    # Interrupts AFTER 'pmf'. User decides next step.
    workflow.add_edge("pmf", END)

    # Compile with Interrupts for HITL Gates
    return workflow.compile(
        interrupt_after=["ideator", "verification", "solution", "pmf"]
    )
