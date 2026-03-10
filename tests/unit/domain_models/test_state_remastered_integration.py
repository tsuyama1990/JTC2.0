import pytest
from pydantic import ValidationError

from src.domain_models.alternative_analysis import AlternativeAnalysis, AlternativeTool
from src.domain_models.enums import Phase
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.state import GlobalState


def test_global_state_remastered_fields() -> None:
    """Verify that Remastered fields can be set correctly and validated."""
    state = GlobalState(topic="Test")
    assert state.alternative_analysis is None
    assert state.value_proposition is None

    tool = AlternativeTool(
        name="Tool Name for Testing",
        financial_cost="Financial Cost of Tool",
        time_cost="Time Cost to switch",
        ux_friction="UX Friction is high",
    )
    state.alternative_analysis = AlternativeAnalysis(
        current_alternatives=[tool],
        switching_cost="High cost of switching tool",
        ten_x_value="Value is huge beyond belief",
    )

    assert state.alternative_analysis is not None
    assert state.alternative_analysis.switching_cost == "High cost of switching tool"


def test_global_state_transition_validation_verification() -> None:
    """Verify state transition missing required data for Verification Phase should raise error."""
    state = GlobalState(topic="Transition Test")
    state.phase = Phase.VERIFICATION
    with pytest.raises(ValidationError):
        GlobalState.model_validate(state.model_dump())


def test_global_state_transition_validation_solution() -> None:
    """Verify state transition missing Persona for Solution Phase should raise error."""
    state = GlobalState(topic="Transition Test")
    state.selected_idea = LeanCanvas(
        id=1,
        title="App",
        problem="P P P",
        solution="S S S",
        customer_segments="C C C",
        unique_value_prop="U U U",
    )
    state.phase = Phase.SOLUTION
    with pytest.raises(ValidationError):
        GlobalState.model_validate(state.model_dump())


@pytest.fixture
def invalid_alternative_tool_data() -> dict[str, str]:
    """Returns organically invalid data for the AlternativeTool model."""
    return {
        "name": "Invalid Short Name",
        "financial_cost": "A",  # Triggers min_length=3 validation dynamically
        "time_cost": "B",
        "ux_friction": "C",
    }


def test_global_state_invalid_assignment(invalid_alternative_tool_data: dict[str, str]) -> None:
    """Ensure strict validation rejects dynamically malformed assignments using descriptive testing inputs."""
    with pytest.raises(ValidationError):
        AlternativeTool(**invalid_alternative_tool_data)
