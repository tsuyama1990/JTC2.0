"""
Integration tests for the Simulation Logic (Turn-based Battle).
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.simulation import create_simulation_graph
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.simulation import DialogueMessage, Role
from src.domain_models.state import GlobalState


@pytest.fixture
def initial_state() -> GlobalState:
    return GlobalState(
        topic="Integration Test",
        selected_idea=LeanCanvas(
            id=1,
            title="Test Idea",
            problem="Problem statement must be long enough.",
            solution="Solution description must be long enough.",
            customer_segments="Segments description here.",
            unique_value_prop="Unique Value Proposition here.",
        ),
        simulation_active=True,
    )


@patch("src.core.simulation.SalesAgent")
@patch("src.core.simulation.FinanceAgent")
@patch("src.core.simulation.NewEmployeeAgent")
@patch("src.core.simulation.get_llm")
def test_simulation_turn_sequence(
    mock_get_llm: MagicMock,
    mock_new_emp_cls: MagicMock,
    mock_finance_cls: MagicMock,
    mock_sales_cls: MagicMock,
    initial_state: GlobalState,
) -> None:
    """
    Verify that the simulation graph executes the correct sequence of turns:
    Pitch -> Finance -> Defense 1 -> Sales -> Defense 2 -> END.
    """
    # Create Mock Instances
    mock_new_emp = MagicMock()
    mock_finance = MagicMock()
    mock_sales = MagicMock()

    mock_new_emp_cls.return_value = mock_new_emp
    mock_finance_cls.return_value = mock_finance
    mock_sales_cls.return_value = mock_sales

    def agent_run_side_effect(role: Role):
        def _run(state: GlobalState):
            msg = DialogueMessage(role=role, content=f"Message from {role}", timestamp=0.0)
            # Simulating what PersonaAgent does: return full updated list
            new_history = list(state.debate_history) + [msg]
            return {"debate_history": new_history}
        return _run

    mock_new_emp.run.side_effect = agent_run_side_effect(Role.NEW_EMPLOYEE)
    mock_finance.run.side_effect = agent_run_side_effect(Role.FINANCE)
    mock_sales.run.side_effect = agent_run_side_effect(Role.SALES)

    # Create the graph
    app = create_simulation_graph()

    # Run the graph
    final_state_dict = app.invoke(initial_state)
    debate_history = final_state_dict["debate_history"]

    assert len(debate_history) == 5

    # Verify order
    roles = [msg.role for msg in debate_history]
    expected_roles = [
        Role.NEW_EMPLOYEE,  # Pitch
        Role.FINANCE,       # Critique
        Role.NEW_EMPLOYEE,  # Defense 1
        Role.SALES,         # Critique
        Role.NEW_EMPLOYEE,  # Defense 2
    ]

    assert roles == expected_roles
    assert debate_history[0].content == f"Message from {Role.NEW_EMPLOYEE}"
    assert debate_history[1].content == f"Message from {Role.FINANCE}"


@patch("src.core.simulation.NewEmployeeAgent")
@patch("src.core.simulation.get_llm")
def test_simulation_error_handling(
    mock_get_llm: MagicMock,
    mock_new_emp_cls: MagicMock,
    initial_state: GlobalState
) -> None:
    """
    Verify that the simulation graph raises exceptions if an agent fails.
    The outer graph wrapper (safe_simulation_run) handles catching,
    but the internal graph should propagate or fail.
    """
    mock_get_llm.return_value = MagicMock()

    # Simulate an agent raising an exception during run
    mock_agent = MagicMock()
    mock_new_emp_cls.return_value = mock_agent
    mock_agent.run.side_effect = RuntimeError("Simulation Crash")

    app = create_simulation_graph()

    with pytest.raises(RuntimeError, match="Simulation Crash"):
        app.invoke(initial_state)
