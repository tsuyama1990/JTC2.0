import pytest
from pydantic import ValidationError

from src.core.config import settings
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
            bio="Sh",  # Too short
        )
    errors = exc.value.errors()
    assert any(e["loc"] == ("name",) for e in errors)
    assert any(e["loc"] == ("occupation",) for e in errors)
    assert any(e["loc"] == ("goals",) for e in errors)
    assert any(e["loc"] == ("bio",) for e in errors)


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


def test_mvp_feature_validation() -> None:
    """Test feature validation."""
    # settings.validation.min_content_length is 3. "Short" is 5.
    # We need a string shorter than 3 characters to trigger the error.
    with pytest.raises(ValidationError):
        Feature(
            name="Login",
            description="No",  # Length 2 < 3
            priority=Priority.MUST_HAVE,
        )


def test_mvp_invalid_priority() -> None:
    """Test that invalid priority strings are rejected."""
    with pytest.raises(ValidationError):
        Feature(
            name="Login",
            description="Login feature description.",
            priority="super-important",
        )


def test_metrics_creation() -> None:
    metrics = Metrics(
        aarrr=AARRR(acquisition=100.0, activation=50.0), custom_metrics={"nps": 9.0}
    )
    assert metrics.aarrr.acquisition == 100.0
    assert metrics.custom_metrics["nps"] == 9.0


def test_metrics_numeric_validation() -> None:
    """Test numeric range validation."""
    with pytest.raises(ValidationError) as exc:
        AARRR(acquisition=-10.0, retention=150.0)

    errors = exc.value.errors()
    assert any(e["loc"] == ("acquisition",) for e in errors)
    assert any(e["loc"] == ("retention",) for e in errors)


def test_metrics_limit_custom() -> None:
    """Test that custom metrics are limited."""
    # Create a dict with VAL_MAX_CUSTOM_METRICS + 1 entries
    excessive_metrics = {
        f"metric_{i}": float(i) for i in range(settings.validation.max_custom_metrics + 1)
    }

    with pytest.raises(ValidationError) as exc:
        Metrics(custom_metrics=excessive_metrics)

    assert "Too many custom metrics" in str(exc.value)


def test_global_state_lifecycle_validation() -> None:
    """Test GlobalState phase transition validation."""
    state = GlobalState()
    assert state.phase == Phase.IDEATION

    # Should allow VERIFICATION transition only with persona
    state.phase = Phase.VERIFICATION
    with pytest.raises(ValidationError) as exc:
        GlobalState.model_validate(state.model_dump())
    assert settings.errors.missing_persona in str(exc.value)

    # Correct transition
    state.target_persona = Persona(
        name="Alice",
        occupation="Manager",
        demographics="40, Female, London",
        goals=["Efficiency"],
        frustrations=["Slow tools"],
        bio="Experienced manager.",
    )
    state.phase = Phase.VERIFICATION
    # Should pass now
    GlobalState.model_validate(state.model_dump())

    # Should allow SOLUTION transition only with MVP
    state.phase = Phase.SOLUTION
    with pytest.raises(ValidationError) as exc:
        GlobalState.model_validate(state.model_dump())
    assert settings.errors.missing_mvp in str(exc.value)
