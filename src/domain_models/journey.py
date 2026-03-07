from pydantic import BaseModel, ConfigDict, Field


class MentalTower(BaseModel):
    model_config = ConfigDict(extra="forbid")

    belief: str = Field(..., min_length=3)
    cognitive_tasks: list[str] = Field(..., min_length=1)


class MentalModelDiagram(BaseModel):
    model_config = ConfigDict(extra="forbid")

    towers: list[MentalTower] = Field(..., min_length=1)
    feature_alignment: str = Field(..., min_length=10)


class JourneyPhase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phase_name: str = Field(..., min_length=3)
    touchpoint: str = Field(..., min_length=3)
    customer_action: str = Field(..., min_length=3)
    mental_tower_ref: str = Field(..., min_length=3)
    pain_points: list[str] = Field(..., min_length=1)
    emotion_score: int = Field(..., ge=-5, le=5)


class CustomerJourney(BaseModel):
    model_config = ConfigDict(extra="forbid")

    phases: list[JourneyPhase] = Field(..., min_length=1)
    worst_pain_phase: str = Field(..., min_length=3)
