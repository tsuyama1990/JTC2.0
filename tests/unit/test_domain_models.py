import pytest
from pydantic import ValidationError

from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.state import GlobalState, Phase


def test_lean_canvas_valid() -> None:
    """Test valid LeanCanvas creation."""
    canvas = LeanCanvas(
        id=1,
        title="Test Idea",
        problem="Test Problem",
        customer_segments="Test Segment",
        unique_value_prop="Test UVP",
        solution="Test Solution",
    )
    assert canvas.id == 1
    assert canvas.title == "Test Idea"
    assert canvas.status == "draft"


def test_lean_canvas_invalid_missing_field() -> None:
    """Test LeanCanvas validation error for missing fields."""
    with pytest.raises(ValidationError):
        LeanCanvas(
            id=1,
            title="Test Idea",
            # Missing problem
            customer_segments="Test Segment",
            unique_value_prop="Test UVP",
            solution="Test Solution",
        )  # type: ignore[call-arg]


def test_lean_canvas_extra_field() -> None:
    """Test LeanCanvas validation error for extra fields."""
    with pytest.raises(ValidationError):
        LeanCanvas(
            id=1,
            title="Test Idea",
            problem="Test Problem",
            customer_segments="Test Segment",
            unique_value_prop="Test UVP",
            solution="Test Solution",
            extra_field="Should fail",  # Extra field
        )  # type: ignore[call-arg]


def test_global_state_defaults() -> None:
    """Test GlobalState default values."""
    state = GlobalState()
    assert state.phase == Phase.IDEATION
    assert state.generated_ideas == []
    assert state.selected_idea is None


def test_global_state_phase_enum() -> None:
    """Test GlobalState uses Phase enum."""
    state = GlobalState(phase=Phase.VERIFICATION)
    assert state.phase == "verification"
    assert isinstance(state.phase, Phase)
