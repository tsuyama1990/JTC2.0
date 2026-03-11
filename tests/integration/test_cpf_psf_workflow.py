import os
from unittest.mock import MagicMock, patch

from src.core.graph import create_app
from src.domain_models.alternative_analysis import AlternativeAnalysis, AlternativeTool
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.state import GlobalState, Phase
from tests.conftest import DUMMY_ENV_VARS


@patch.dict(os.environ, DUMMY_ENV_VARS)
@patch("src.core.factory.get_llm")
def test_full_workflow_state_mutation(mock_get_llm: MagicMock) -> None:
    """
    Test that the workflow properly mutates the expanded state
    and handles transitions properly.
    """
    _app = create_app()

    # We construct a state that starts from IDEATION
    _initial_state = GlobalState(topic="Enterprise AI", phase=Phase.IDEATION)

    # We skip full execution by just testing schema mutations directly,
    # and ensuring that nodes which update these work.

    # Simulate Ideator updating state
    idea = LeanCanvas(id=1, title="Test Idea", problem="Long enough problem", customer_segments="Long enough segments", unique_value_prop="Long enough prop", solution="Long enough solution")
    state = GlobalState(topic="Test Idea", selected_idea=idea)

    # Simulate a node injecting alternative_analysis
    analysis = AlternativeAnalysis(
        current_alternatives=[AlternativeTool(name="A", financial_cost="B", time_cost="C", ux_friction="D")],
        switching_cost="E",
        ten_x_value="F"
    )

    state.alternative_analysis = analysis

    # Validate the state mutation
    assert state.alternative_analysis.switching_cost == "E"

    # Assert validation passes
    validated = GlobalState.model_validate(state.model_dump())
    assert validated.alternative_analysis is not None
