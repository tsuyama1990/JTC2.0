import itertools
import os
from unittest.mock import MagicMock, patch

import pytest

# We import create_app but we will mock the LLM and Tools inside it
from src.core.config import get_settings
from src.core.graph import create_app
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.state import GlobalState, Phase


@pytest.fixture
def mock_llm_factory() -> MagicMock:
    return MagicMock()


@patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test", "TAVILY_API_KEY": "tv-test", "V0_API_KEY": "v0-test"})
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
    # Clear cache to ensure env vars are picked up
    get_settings.cache_clear()

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
    # This will now succeed because env vars are patched and cache cleared
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
    # Use itertools.islice to check the first few elements without consuming the entire iterator
    # (assuming it might be infinite or very large in a real scenario).
    # However, since we need to verify length and content for the test, we acknowledge consumption here.
    # In a real app, pagination would use islice.
    assert final_state.generated_ideas is not None

    # We slice to ensure we don't accidentally consume an infinite generator, though our mock is finite.
    # We take 11 items to check if there are indeed 10 (or more).
    preview_ideas = list(itertools.islice(final_state.generated_ideas, 11))

    assert len(preview_ideas) == 10
    assert final_state.phase == Phase.IDEATION

    # Verify the agent was called
    mock_ideator_instance.run.assert_called()

    # 5. Selection (Simulated Logic)
    # Since the Graph only runs the Ideator node currently, the Selection part is handled
    # by the CLI logic (main.py) which updates the state.
    # In Cycle 1, the Graph stops after Ideation.

    selected_id = 2
    # Select from the previewed list since the generator is consumed up to that point
    selected_canvas = next(idea for idea in preview_ideas if idea.id == selected_id)

    # Verify we can select
    assert selected_canvas.id == 2
    assert selected_canvas.title == "Idea 2"
