"""
Integration tests for the Simulation Logic (Turn-based Battle).
"""

from unittest.mock import MagicMock, patch

import pytest

from src.core.simulation import create_simulation_graph
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.simulation import Role
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


@patch("src.core.factory.AgentFactory.get_persona_agent")
def test_simulation_turn_sequence(
    mock_get_persona: MagicMock,
    initial_state: GlobalState,
) -> None:
    """
    Verify that the simulation graph executes the correct sequence of turns:
    Pitch -> Finance -> Defense 1 -> Sales -> Defense 2 -> END.
    """
    # Setup mock agents for each role
    mock_agent = MagicMock()
    mock_agent.run.return_value = {"debate_history": []} # State update

    # We need the graph to actually append messages.
    # But currently the graph nodes call agent.run() which returns state update.
    # The agents append to debate history.
    # So we need our mock to simulate that or we just check the calls.

    # Let's mock the agent to return an updated debate history with a new message
    def side_effect(state):
        import time

        from src.domain_models.simulation import DialogueMessage
        # Determine role from last call? No, side_effect doesn't know.
        # But we can inspect the call args of get_persona_agent?
        # Actually, get_persona_agent is called, returns mock_agent, then .run(state) is called.
        # We can just return a dummy update and verify the sequence of calls to factory.
        new_msg = DialogueMessage(role=Role.NEW_EMPLOYEE, content="Msg", timestamp=time.time())
        return {"debate_history": [*state.debate_history, new_msg]}

    mock_agent.run.side_effect = side_effect
    mock_get_persona.return_value = mock_agent

    app = create_simulation_graph()
    app.invoke(initial_state)

    # Verify sequence of calls to factory
    assert mock_get_persona.call_count == 5

    expected_calls = [
        ((Role.NEW_EMPLOYEE,),),
        ((Role.FINANCE,),),
        ((Role.NEW_EMPLOYEE,),),
        ((Role.SALES,),),
        ((Role.NEW_EMPLOYEE,),),
    ]

    # Check args of each call
    assert [c.args for c in mock_get_persona.call_args_list] == [c[0] for c in expected_calls]


@patch("src.core.factory.AgentFactory.get_persona_agent")
def test_simulation_error_handling(
    mock_get_persona: MagicMock,
    initial_state: GlobalState
) -> None:
    """
    Verify that the simulation graph raises exceptions if an agent fails.
    """
    mock_agent = MagicMock()
    mock_agent.run.side_effect = RuntimeError("Simulation Crash")
    mock_get_persona.return_value = mock_agent

    app = create_simulation_graph()

    with pytest.raises(RuntimeError, match="Simulation Crash"):
        app.invoke(initial_state)
