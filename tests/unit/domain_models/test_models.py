import pytest
from pydantic import ValidationError

from src.domain_models.persona import EmpathyMap, Persona


def test_persona_creation() -> None:
    empathy = EmpathyMap(
        says=["I want this"],
        thinks=["Is it worth it?"],
        does=["Search online"],
        feels=["Confused"],
    )
    persona = Persona(
        name="John Doe",
        occupation="Developer",
        demographics="30, Male, New York",
        goals=["Learn Python"],
        frustrations=["No time"],
        bio="A busy developer looking to improve skills.",
        empathy_map=empathy,
        is_fact_based=True,
        interview_insights=["Insight 1"],
    )
    assert persona.name == "John Doe"
    assert persona.empathy_map is not None
    assert persona.empathy_map.says == ["I want this"]
    assert persona.is_fact_based is True
    assert len(persona.interview_insights) == 1


def test_persona_validation_error() -> None:
    """Test validation limits for Persona."""
    with pytest.raises(ValidationError) as exc:
        Persona(
            name="J",  # Too short
            occupation="D",
            demographics="M",
            goals=[],  # Empty
            frustrations=[],
            bio="Sh",  # Too short
        )
    errors = exc.value.errors()
    assert any(e["loc"] == ("name",) for e in errors)
    assert any(e["loc"] == ("occupation",) for e in errors)
    assert any(e["loc"] == ("goals",) for e in errors)
    assert any(e["loc"] == ("bio",) for e in errors)
