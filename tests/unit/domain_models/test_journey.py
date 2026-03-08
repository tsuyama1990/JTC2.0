import pytest
from pydantic import ValidationError

from src.domain_models.journey import CustomerJourney, JourneyPhase


def test_journey_phase_valid() -> None:
    phase = JourneyPhase(
        phase_name="Discovery",
        touchpoint="Google Search",
        customer_action="Searches for data automation tools",
        mental_tower_ref="Needs to save time",
        pain_points=["Too many options", "Hard to tell which are good"],
        emotion_score=-2,
    )
    assert phase.emotion_score == -2


def test_journey_phase_invalid_emotion_score() -> None:
    with pytest.raises(ValidationError):
        JourneyPhase(
            phase_name="Discovery",
            touchpoint="Google Search",
            customer_action="Searches for data automation tools",
            mental_tower_ref="Needs to save time",
            pain_points=["Too many options"],
            emotion_score=6,  # out of range (-5 to 5)
        )


def test_customer_journey_valid() -> None:
    phase1 = JourneyPhase(
        phase_name="Discovery",
        touchpoint="Google",
        customer_action="Search",
        mental_tower_ref="Needs time",
        pain_points=["Options"],
        emotion_score=0,
    )
    phase2 = JourneyPhase(
        phase_name="Trial",
        touchpoint="Website",
        customer_action="Sign up",
        mental_tower_ref="Needs easy tool",
        pain_points=["Form too long"],
        emotion_score=-3,
    )
    phase3 = JourneyPhase(
        phase_name="Onboarding",
        touchpoint="App",
        customer_action="First task",
        mental_tower_ref="Needs success",
        pain_points=["Confusing UI"],
        emotion_score=-1,
    )
    journey = CustomerJourney(
        phases=[phase1, phase2, phase3],
        worst_pain_phase="Trial",
    )
    assert len(journey.phases) == 3


def test_customer_journey_invalid_length() -> None:
    phase1 = JourneyPhase(
        phase_name="Discovery",
        touchpoint="Google",
        customer_action="Search",
        mental_tower_ref="Needs time",
        pain_points=["Options"],
        emotion_score=0,
    )
    with pytest.raises(ValidationError):
        CustomerJourney(
            phases=[phase1],  # min_length=3
            worst_pain_phase="Discovery",
        )
