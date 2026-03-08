"""
Customer Journey models.
"""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.core.config import get_settings


class JourneyPhase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phase_name: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="Phase name (e.g., Awareness, Consideration, Using, Churn)",
    )
    touchpoint: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="Point of contact between the customer and the system/environment",
    )
    customer_action: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="Specific action of the customer",
    )
    mental_tower_ref: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="The belief in the MentalTower backing this action",
    )
    pain_points: list[str] = Field(
        ...,
        min_length=get_settings().validation.min_list_length,
        description="Pains or frustrations felt in this phase",
    )
    emotion_score: int = Field(
        ...,
        ge=-5,
        le=5,
        description="Emotional fluctuation (-5 to 5)",
    )


class CustomerJourney(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phases: list[JourneyPhase] = Field(
        ...,
        min_length=3,
        max_length=7,
        description="Sequential phases in the customer journey",
    )
    worst_pain_phase: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="Name of the phase where the Pain is the deepest (and must be solved)",
    )

    @model_validator(mode="after")
    def validate_worst_pain_phase(self) -> Self:
        """Ensure worst_pain_phase matches an existing phase_name in phases."""
        valid_phase_names = {phase.phase_name for phase in self.phases}
        if self.worst_pain_phase not in valid_phase_names:
            msg = f"worst_pain_phase '{self.worst_pain_phase}' does not match any existing phase name."
            raise ValueError(msg)
        return self
