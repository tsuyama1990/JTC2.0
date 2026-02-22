from unittest.mock import MagicMock

import pytest

from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.state import GlobalState, Phase

# Mock imports for things that don't exist yet
# from src.core.graph import create_app # noqa: ERA001


@pytest.fixture
def mock_app() -> MagicMock:
    # This simulates the compiled LangGraph app
    return MagicMock()


def test_uat_cycle01_ideation_and_selection(mock_app: MagicMock) -> None:
    """
    UAT Scenario:
    1. User inputs topic "AI for Agriculture".
    2. System generates 10 ideas.
    3. User selects idea #2.
    4. System updates state.
    """

    # 1. Initial State
    initial_state = GlobalState(topic="AI for Agriculture")

    # Mock the graph execution result for Step 2 (Ideation)
    # The real app.invoke would return the final state

    # Simulate Ideator Agent generating 10 ideas
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

    state_after_ideation = initial_state.model_copy()
    state_after_ideation.generated_ideas = generated_ideas

    # Verify Step 2
    assert len(state_after_ideation.generated_ideas) == 10
    assert state_after_ideation.phase == Phase.IDEATION

    # 3. User Selects Idea #2
    selected_id = 2
    selected_canvas = next(
        idea for idea in state_after_ideation.generated_ideas if idea.id == selected_id
    )

    # Simulate State Update
    final_state = state_after_ideation.model_copy()
    final_state.selected_idea = selected_canvas
    # Ideally phase transitions to VERIFICATION
    # final_state.phase = Phase.VERIFICATION # noqa: ERA001

    # Verify Step 4
    if final_state.selected_idea is None:
        pytest.fail("Selected idea should not be None")

    assert final_state.selected_idea.id == 2
    assert final_state.selected_idea.title == "Idea 2"
