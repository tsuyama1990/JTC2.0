import pytest
from pydantic import ValidationError

from src.domain_models.journey import CustomerJourney, JourneyPhase, MentalModelDiagram, MentalTower


def test_mental_tower() -> None:
    tower = MentalTower(
        belief="Time is money", cognitive_tasks=["Checking schedule", "Estimating delay"]
    )
    assert tower.belief == "Time is money"

    with pytest.raises(ValidationError):
        MentalTower(belief="Hi", cognitive_tasks=[])


def test_mental_model_diagram() -> None:
    tower = MentalTower(belief="Time is money", cognitive_tasks=["Checking schedule"])
    diagram = MentalModelDiagram(
        towers=[tower], feature_alignment="The feature aligns nicely with saving time."
    )
    assert len(diagram.towers) == 1

    with pytest.raises(ValidationError):
        MentalModelDiagram(towers=[], feature_alignment="Too short")


def test_journey_phase() -> None:
    phase = JourneyPhase(
        phase_name="Discovery",
        touchpoint="Google Search",
        customer_action="Searching for solutions",
        mental_tower_ref="Time is money",
        pain_points=["Hard to find info"],
        emotion_score=-3,
    )
    assert phase.emotion_score == -3

    with pytest.raises(ValidationError):
        JourneyPhase(
            phase_name="Hi",
            touchpoint="Google Search",
            customer_action="Searching for solutions",
            mental_tower_ref="Time is money",
            pain_points=["Hard to find info"],
            emotion_score=-10,
        )


def test_customer_journey() -> None:
    phase = JourneyPhase(
        phase_name="Discovery",
        touchpoint="Google Search",
        customer_action="Searching for solutions",
        mental_tower_ref="Time is money",
        pain_points=["Hard to find info"],
        emotion_score=-3,
    )
    journey = CustomerJourney(phases=[phase], worst_pain_phase="Discovery")
    assert journey.worst_pain_phase == "Discovery"

    with pytest.raises(ValidationError):
        CustomerJourney(phases=[], worst_pain_phase="Discovery")
