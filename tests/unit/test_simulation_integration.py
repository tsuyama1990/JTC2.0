"""
Integration tests for the Simulation Logic (Turn-based Battle).
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.simulation import _get_cached_agent, create_simulation_graph
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


@patch("src.core.simulation.get_llm")
def test_simulation_turn_sequence(
    mock_get_llm: MagicMock,
    initial_state: GlobalState,
) -> None:
    """
    Verify that the simulation graph executes the correct sequence of turns:
    Pitch -> Finance -> Defense 1 -> Sales -> Defense 2 -> END.

    We use REAL agent classes but mock the LLM inside them.
    """
    _get_cached_agent.cache_clear()

    # Mock the LLM to return a predictable response based on input prompts (optional)
    # or just generic response
    mock_llm = MagicMock()
    mock_llm.invoke.return_value.content = "Mocked Response"
    mock_get_llm.return_value = mock_llm

    # Create the graph (it will instantiate real agents which use the mocked LLM)
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
    _get_cached_agent.cache_clear()

    mock_get_llm.return_value = MagicMock()

    # Simulate an agent raising an exception during run
    mock_agent = MagicMock()
    mock_new_emp_cls.return_value = mock_agent
    mock_agent.run.side_effect = RuntimeError("Simulation Crash")

    app = create_simulation_graph()

    with pytest.raises(RuntimeError, match="Simulation Crash"):
        app.invoke(initial_state)
