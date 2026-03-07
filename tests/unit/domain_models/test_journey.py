import pytest
from pydantic import ValidationError

from src.domain_models.journey import CustomerJourney, JourneyPhase, MentalModelDiagram, MentalTower


def test_mental_tower() -> None:
    tower = MentalTower(
        belief="Time is money",
        cognitive_tasks=["Checking schedule", "Estimating delay", "Planning route"],
    )
    assert tower.belief == "Time is money"

    with pytest.raises(ValidationError):
        MentalTower(belief="Hi", cognitive_tasks=[])


def test_mental_model_diagram() -> None:
    tower = MentalTower(
        belief="Time is money",
        cognitive_tasks=["Checking schedule", "Estimating delay", "Planning route"],
    )
    tower2 = MentalTower(
        belief="Trust is earned",
        cognitive_tasks=["Reading reviews", "Checking prices", "Comparing specs"],
    )
    tower3 = MentalTower(
        belief="Convenience is key",
        cognitive_tasks=["One click buy", "Fast shipping", "Easy returns"],
    )
    diagram = MentalModelDiagram(
        towers=[tower, tower2, tower3],
        feature_alignment="The feature aligns nicely with saving time.",
    )
    assert len(diagram.towers) == 3

    with pytest.raises(ValidationError):
        MentalModelDiagram(towers=[], feature_alignment="Too short")


def test_journey_phase() -> None:
    phase = JourneyPhase(
        phase_name="Discovery",
        touchpoint="Google Search",
        customer_action="Searching for solutions",
        mental_tower_ref="Time is money",
        pain_points=["Hard to find info", "No clear pricing", "Slow website"],
        emotion_score=-3,
    )
    assert phase.emotion_score == -3

    with pytest.raises(ValidationError):
        JourneyPhase(
            phase_name="Hi",
            touchpoint="Google Search",
            customer_action="Searching for solutions",
            mental_tower_ref="Time is money",
            pain_points=["Hard to find info", "No clear pricing", "Slow website"],
            emotion_score=-10,
        )


def test_customer_journey() -> None:
    phase1 = JourneyPhase(
        phase_name="Discovery",
        touchpoint="Google Search",
        customer_action="Searching for solutions",
        mental_tower_ref="Time is money",
        pain_points=["Hard to find info", "No clear pricing", "Slow website"],
        emotion_score=-3,
    )
    phase2 = JourneyPhase(
        phase_name="Evaluation",
        touchpoint="Landing Page",
        customer_action="Reading features",
        mental_tower_ref="Trust is earned",
        pain_points=["Missing details", "Confusing terms", "No demo"],
        emotion_score=-1,
    )
    phase3 = JourneyPhase(
        phase_name="Purchase",
        touchpoint="Checkout Page",
        customer_action="Entering payment",
        mental_tower_ref="Convenience is key",
        pain_points=["Too many fields", "Card declined", "No paypal"],
        emotion_score=2,
    )
    journey = CustomerJourney(phases=[phase1, phase2, phase3], worst_pain_phase="Discovery")
    assert journey.worst_pain_phase == "Discovery"

    with pytest.raises(ValidationError):
        CustomerJourney(phases=[], worst_pain_phase="Discovery")
