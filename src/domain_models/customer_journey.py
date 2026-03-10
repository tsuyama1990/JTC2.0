"""
Customer Journey models.
"""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class JourneyPhase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phase_name: str = Field(
        ...,
        description="Phase name (e.g., Awareness, Consideration, Using, Churn)",
    )
    touchpoint: str = Field(
        ...,
        description="Point of contact between the customer and the system/environment",
    )
    customer_action: str = Field(
        ...,
        description="Specific action of the customer",
    )
    mental_tower_ref: str = Field(
        ...,
        description="The belief in the MentalTower backing this action",
    )
    pain_points: list[str] = Field(
        ...,
        description="Pains or frustrations felt in this phase",
    )
    emotion_score: int = Field(
        ...,
        ge=-5,
        le=5,
        description="Emotional fluctuation (-5 to 5)",
    )

    @model_validator(mode="after")
    def validate_lengths(self) -> Self:

        for field in ["phase_name", "touchpoint", "customer_action", "mental_tower_ref"]:
            val = getattr(self, field)
            if isinstance(val, str) and len(val) < 10:
                msg = f"{field} must be at least {10} characters"
                raise ValueError(msg)

        if len(self.pain_points) < 1:
            msg = f"pain_points must contain at least {1} items"
            raise ValueError(msg)

        return self


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
        description="Name of the phase where the Pain is the deepest (and must be solved)",
    )

    @model_validator(mode="after")
    def validate_worst_pain_phase(self) -> Self:
        """Ensure worst_pain_phase matches an existing phase_name in phases."""
        valid_phase_names = {phase.phase_name for phase in self.phases}
        if self.worst_pain_phase not in valid_phase_names:
            msg = f"worst_pain_phase '{self.worst_pain_phase}' does not match any existing phase name."
            raise ValueError(msg)

        if len(self.worst_pain_phase) < 10:
            msg = "worst_pain_phase must be at least 10 characters"
            raise ValueError(msg)

        return self
