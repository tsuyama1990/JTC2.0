import pytest
from pydantic import ValidationError

from src.domain_models.simulation import DialogueMessage, Role
from src.domain_models.state import GlobalState
from src.domain_models.lean_canvas import LeanCanvas


def test_dialogue_message_valid() -> None:
    """Test creating a valid DialogueMessage."""
    msg = DialogueMessage(
        role=Role.FINANCE,
        content="This idea is too expensive.",
        timestamp=1234567890.0,
    )
    assert msg.role == Role.FINANCE
    assert msg.content == "This idea is too expensive."
    assert msg.timestamp == 1234567890.0


def test_dialogue_message_invalid_role() -> None:
    """Test DialogueMessage with invalid role."""
    with pytest.raises(ValidationError):
        DialogueMessage(
            role="Janitor",
            content="Cleaning up.",
            timestamp=123.0,
        )


def test_dialogue_message_empty_content() -> None:
    """Test DialogueMessage with empty content."""
    with pytest.raises(ValidationError):
        DialogueMessage(
            role=Role.NEW_EMPLOYEE,
            content="",
            timestamp=123.0,
        )


def test_dialogue_message_extra_fields() -> None:
    """Test DialogueMessage with extra fields (should be forbidden)."""
    with pytest.raises(ValidationError):
        DialogueMessage(
            role=Role.CPO,
            content="Valid content.",
            timestamp=123.0,
            extra_field="Should fail",  # type: ignore[call-arg]
        )


def test_global_state_serialization() -> None:
    """Test that GlobalState can be serialized and deserialized."""
    # Create a complex state
    idea = LeanCanvas(
        id=1,
        title="Test Idea",
        problem="Problem statement here.",
        customer_segments="Segments here.",
        unique_value_prop="UVP statement here.",
        solution="Solution statement here.",
    )
    msg1 = DialogueMessage(role=Role.NEW_EMPLOYEE, content="Hi", timestamp=100.0)
    msg2 = DialogueMessage(role=Role.FINANCE, content="Cost?", timestamp=101.5)

    state = GlobalState(
        topic="Test Topic",
        selected_idea=idea,
        debate_history=[msg1, msg2],
        simulation_active=True
    )

    # Serialize
    json_str = state.model_dump_json()
    assert "Test Topic" in json_str
    assert "Cost?" in json_str

    # Deserialize
    restored_state = GlobalState.model_validate_json(json_str)

    # Check equality
    assert restored_state.topic == state.topic
    assert restored_state.selected_idea == state.selected_idea
    assert len(restored_state.debate_history) == 2
    assert restored_state.debate_history[1].role == Role.FINANCE
    assert restored_state.debate_history[1].timestamp == 101.5
