
import pytest
from pydantic import ValidationError

from src.domain_models.transcript import Transcript


def test_transcript_valid() -> None:
    """Test valid transcript creation."""
    t = Transcript(
        source="Interview with John",
        content="I love this product very much.",
        date="2023-10-27"
    )
    assert t.source == "Interview with John"
    assert "love" in t.content


def test_transcript_content_too_short() -> None:
    """Test content length validation."""
    with pytest.raises(ValidationError) as exc:
        Transcript(
            source="Test",
            content="Too short",
            date="2023-10-27"
        )
    assert "Transcript content is too short" in str(exc.value)


def test_transcript_extra_fields() -> None:
    """Test that extra fields are forbidden."""
    with pytest.raises(ValidationError):
        Transcript(
            source="Test",
            content="Valid content here.",
            date="2023-10-27",
            extra_field="Should fail"  # type: ignore
        )
