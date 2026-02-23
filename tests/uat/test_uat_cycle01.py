from unittest.mock import MagicMock, patch

import pytest

# We import create_app but we will mock the LLM and Tools inside it
from src.core.graph import create_app
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.state import GlobalState, Phase


@pytest.fixture
def mock_llm_factory() -> MagicMock:
    return MagicMock()


@patch("src.core.graph.IdeatorAgent")
@patch("src.core.graph.get_llm")
def test_uat_cycle01_ideation_and_selection(
    mock_get_llm: MagicMock, mock_ideator_cls: MagicMock
) -> None:
    """
    UAT Scenario:
    1. User inputs topic "AI for Agriculture".
    2. System generates 10 ideas.
    3. User selects idea #2.
    4. System updates state.

    This integration test runs the actual LangGraph compiled app,
    but mocks the external LLM and Search calls via the IdeatorAgent mock.
    """

    # 1. Setup Logic Mock
    mock_ideator_instance = mock_ideator_cls.return_value

    generated_ideas = [
        LeanCanvas(
            id=i,
            title=f"Idea {i}",
            problem="Problem statement text",
            customer_segments="Customer Segments",
            unique_value_prop="Unique Value Proposition",
            solution="Solution description text",
        )
        for i in range(10)
    ]

    # The agent run method returns a dict update
    # IMPORTANT: We must return an iterator here because GlobalState expects Iterator[LeanCanvas]
    mock_ideator_instance.run.return_value = {"generated_ideas": iter(generated_ideas)}

    # 2. Build App
    app = create_app()

    # 3. Execution (Step 1 & 2)
    initial_state = GlobalState(topic="AI for Agriculture")
    final_state_dict = app.invoke(initial_state)

    # Convert dict back to State model for assertion convenience
    # (LangGraph returns dict by default in compiled graph unless configured otherwise)
    if isinstance(final_state_dict, dict):
        final_state = GlobalState(**final_state_dict)
    else:
        final_state = final_state_dict  # Should not happen with default LangGraph

    # 4. Verification
    # Since generated_ideas is now an Iterable, we convert to list to check length
    # Note: Consuming the iterator here means final_state.generated_ideas is exhausted
    # unless we re-populate it or use the consumed list for further checks.
    assert final_state.generated_ideas is not None
    ideas_list = list(final_state.generated_ideas)
    assert len(ideas_list) == 10
    assert final_state.phase == Phase.IDEATION

    # Verify the agent was called
    mock_ideator_instance.run.assert_called()

    # 5. Selection (Simulated Logic)
    # Since the Graph only runs the Ideator node currently, the Selection part is handled
    # by the CLI logic (main.py) which updates the state.
    # In Cycle 1, the Graph stops after Ideation.

    selected_id = 2
    # We must select from the captured list because final_state.generated_ideas generator is consumed above
    selected_canvas = next(idea for idea in ideas_list if idea.id == selected_id)

    # Verify we can select
    assert selected_canvas.id == 2
    assert selected_canvas.title == "Idea 2"
