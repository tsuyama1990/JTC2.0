import pytest
from pydantic import ValidationError

from src.domain_models.metrics import AARRR, Metrics
from src.domain_models.mvp import MVP, Feature, MVPType
from src.domain_models.persona import EmpathyMap, Persona


def test_persona_creation() -> None:
    empathy = EmpathyMap(
        says=["I want this"], thinks=["Is it worth it?"], does=["Search online"], feels=["Confused"]
    )
    persona = Persona(
        name="John Doe",
        occupation="Developer",
        demographics="30, Male",
        goals=["Learn Python"],
        frustrations=["No time"],
        bio="A busy developer.",
        empathy_map=empathy,
    )
    assert persona.name == "John Doe"
    assert persona.empathy_map is not None
    assert persona.empathy_map.says == ["I want this"]


def test_mvp_creation() -> None:
    feature = Feature(name="Login", description="Allow users to login", priority="Must-have")
    mvp = MVP(
        type=MVPType.LANDING_PAGE,
        core_features=[feature],
        success_criteria="100 signups",
    )
    assert mvp.type == MVPType.LANDING_PAGE
    assert mvp.core_features[0].name == "Login"


def test_metrics_creation() -> None:
    metrics = Metrics(
        aarrr=AARRR(acquisition=100.0, activation=50.0),
        custom_metrics={"nps": 9.0}
    )
    assert metrics.aarrr.acquisition == 100.0
    assert metrics.custom_metrics["nps"] == 9.0


def test_invalid_mvp_type() -> None:
    with pytest.raises(ValidationError):
        MVP(
            type="invalid_type",
            core_features=[],
            success_criteria="Fail"
        )
