"""
Defines the Mental Model Diagram domain models.
"""

from pydantic import BaseModel, ConfigDict, Field


class MentalTower(BaseModel):
    model_config = ConfigDict(extra="forbid")
    belief: str = Field(
        ...,
        description="ユーザーの根底にある信念や価値観(例: 『時間を無駄にしたくない』)",
        min_length=2,
    )
    cognitive_tasks: list[str] = Field(
        ...,
        description="その信念に基づいて頭の中で行っているタスクや判断",
        min_length=1,
    )


class MentalModelDiagram(BaseModel):
    model_config = ConfigDict(extra="forbid")
    towers: list[MentalTower] = Field(
        ...,
        description="ユーザーの思考空間を構成する複数の思考の塔",
        min_length=1,
    )
    feature_alignment: str = Field(
        ...,
        description="定義した思考の塔(タワー)に対して、提供する機能がどう寄り添い、サポートしているかのマッピング",
        min_length=3,
    )
