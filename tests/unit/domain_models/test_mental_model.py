import pytest
from pydantic import ValidationError

from src.domain_models.mental_model import MentalModelDiagram, MentalTower


def test_mental_tower_valid() -> None:
    tower = MentalTower(
        belief="Data must be perfectly accurate",
        cognitive_tasks=["Double checking figures", "Cross-referencing spreadsheets"],
    )
    assert tower.belief == "Data must be perfectly accurate"


def test_mental_tower_invalid() -> None:
    with pytest.raises(ValidationError):
        MentalTower(
            belief="Short",  # too short
            cognitive_tasks=["Double checking figures"],
        )


def test_mental_model_diagram_valid() -> None:
    tower = MentalTower(
        belief="Data must be perfectly accurate",
        cognitive_tasks=["Double checking figures", "Cross-referencing spreadsheets"],
    )
    diagram = MentalModelDiagram(
        towers=[tower],
        feature_alignment="The AI automation feature aligns with the desire for perfect accuracy.",
    )
    assert diagram.towers[0].belief == "Data must be perfectly accurate"


def test_mental_model_diagram_invalid() -> None:
    with pytest.raises(ValidationError):
        MentalModelDiagram(
            towers=[],  # invalid length
            feature_alignment="Short",  # too short
        )
