"""
Defines the Customer Journey domain models.
"""

from pydantic import BaseModel, ConfigDict, Field


class JourneyPhase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phase_name: str = Field(
        ...,
        description="フェーズ名(例: 認知、検討、利用中、離脱)",
        min_length=1,
    )
    touchpoint: str = Field(
        ...,
        description="顧客とシステム/環境の接点",
        min_length=1,
    )
    customer_action: str = Field(
        ..., description="顧客の具体的な行動", min_length=1
    )
    mental_tower_ref: str = Field(
        ...,
        description="この行動を裏付けているMentalTowerの信念",
        min_length=1,
    )
    pain_points: list[str] = Field(
        ...,
        description="このフェーズで感じる痛みや不満",
        min_length=1,
    )
    emotion_score: int = Field(..., ge=-5, le=5, description="感情の起伏(-5から5)")


class CustomerJourney(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phases: list[JourneyPhase] = Field(
        ..., min_length=3, max_length=7, description="ジャーニーの各フェーズ"
    )
    worst_pain_phase: str = Field(
        ...,
        description="最もPainが深い(解決すべき)フェーズの名前",
        min_length=1,
    )
