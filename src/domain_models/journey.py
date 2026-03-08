from pydantic import BaseModel, ConfigDict, Field

from src.core.config import get_settings


class JourneyPhase(BaseModel):
    """
    Represents a phase in the customer journey mapping chronologically.
    """

    model_config = ConfigDict(extra="forbid")

    phase_name: str = Field(
        ...,
        description="Name of the journey phase",
        min_length=1,
        max_length=50,
    )
    touchpoint: str = Field(
        ...,
        description="The touchpoint with the customer",
        min_length=1,
        max_length=100,
    )
    customer_action: str = Field(
        ...,
        description="The action the customer takes",
        min_length=1,
        max_length=200,
    )
    mental_tower_ref: str = Field(
        ...,
        description="Reference to a MentalTower",
        min_length=1,
        max_length=50,
    )
    pain_points: list[str] = Field(
        ...,
        description="List of pain points in this phase",
        min_length=get_settings().validation.min_list_length,
        max_length=get_settings().validation.max_list_length,
    )
    emotion_score: int = Field(
        ...,
        description="Emotion score from -5 (worst) to 5 (best)",
        ge=-5,
        le=5,
    )


class CustomerJourney(BaseModel):
    """
    Customer Journey Model. Maps actions chronologically based on mental models.
    """

    model_config = ConfigDict(extra="forbid")

    phases: list[JourneyPhase] = Field(
        ...,
        description="List of phases in the customer journey",
        min_length=3,
        max_length=7,
    )
    worst_pain_phase: str = Field(
        ...,
        description="The name of the phase with the strongest pain",
        min_length=1,
        max_length=50,
    )
