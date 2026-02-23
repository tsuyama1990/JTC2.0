import pytest
from pydantic import ValidationError

from src.core.constants import VAL_MAX_CUSTOM_METRICS
from src.domain_models.metrics import AARRR, Metrics
from src.domain_models.mvp import MVP, Feature, MVPType, Priority
from src.domain_models.persona import EmpathyMap, Persona
from src.domain_models.state import GlobalState, Phase


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
    )
    assert persona.name == "John Doe"
    assert persona.empathy_map is not None
    assert persona.empathy_map.says == ["I want this"]


def test_persona_validation_error() -> None:
    """Test validation limits for Persona."""
    with pytest.raises(ValidationError) as exc:
        Persona(
            name="J",  # Too short
            occupation="D",
            demographics="M",
            goals=[],  # Empty
            frustrations=[],
            bio="Short",  # Too short (assumed default min 3 or 10)
        )
    errors = exc.value.errors()
    assert any(e["loc"] == ("name",) for e in errors)
    assert any(e["loc"] == ("occupation",) for e in errors)


def test_mvp_creation() -> None:
    feature = Feature(
        name="Login System",
        description="Allow users to login via OAuth.",
        priority=Priority.MUST_HAVE,
    )
    mvp = MVP(
        type=MVPType.LANDING_PAGE,
        core_features=[feature],
        success_criteria="Achieve 100 signups within the first week.",
    )
    assert mvp.type == MVPType.LANDING_PAGE
    assert mvp.core_features[0].priority == Priority.MUST_HAVE


def test_mvp_invalid_priority() -> None:
    """Test that invalid priority strings are rejected."""
    with pytest.raises(ValidationError):
        Feature(
            name="Login",
            description="Login feature",
            priority="super-important",
        )


def test_metrics_creation() -> None:
    metrics = Metrics(
        aarrr=AARRR(acquisition=100.0, activation=50.0), custom_metrics={"nps": 9.0}
    )
    assert metrics.aarrr.acquisition == 100.0
    assert metrics.custom_metrics["nps"] == 9.0


def test_metrics_limit_custom() -> None:
    """Test that custom metrics are limited."""
    # Create a dict with VAL_MAX_CUSTOM_METRICS + 1 entries
    excessive_metrics = {f"metric_{i}": float(i) for i in range(VAL_MAX_CUSTOM_METRICS + 1)}

    with pytest.raises(ValidationError) as exc:
        Metrics(custom_metrics=excessive_metrics)

    assert "Too many custom metrics" in str(exc.value)


def test_global_state_lifecycle() -> None:
    """Test GlobalState transitions and field population."""
    state = GlobalState()
    assert state.phase == Phase.IDEATION

    # Simulate transition to Verification
    state.phase = Phase.VERIFICATION
    state.target_persona = Persona(
        name="Alice",
        occupation="Manager",
        demographics="40, Female, London",
        goals=["Efficiency"],
        frustrations=["Slow tools"],
        bio="Experienced manager.",
    )
    assert state.target_persona.name == "Alice"

    # Simulate transition to Solution
    state.phase = Phase.SOLUTION
    state.mvp_definition = MVP(
        type=MVPType.CONCIERGE,
        core_features=[
            Feature(
                name="Manual Onboarding",
                description="We do it for them.",
                priority=Priority.MUST_HAVE,
            )
        ],
        success_criteria="5 paying customers.",
    )
    assert state.mvp_definition.type == "concierge"
