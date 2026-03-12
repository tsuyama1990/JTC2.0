from pydantic import BaseModel, ConfigDict, Field


class CustomerProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_jobs: list[str] = Field(..., description="顧客が片付けたい用事・社会的/感情的タスク")
    pains: list[str] = Field(..., description="ジョブの実行を妨げるリスクやネガティブな感情")
    gains: list[str] = Field(..., description="ジョブの実行によって得たい恩恵や期待")


class ValueMap(BaseModel):
    model_config = ConfigDict(extra="forbid")
    products_and_services: list[str] = Field(
        ..., description="提供する主要な製品・サービスのリスト"
    )
    pain_relievers: list[str] = Field(..., description="顧客のPainを具体的にどう取り除くか")
    gain_creators: list[str] = Field(..., description="顧客のGainを具体的にどう創出するか")


class ValuePropositionCanvas(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_profile: CustomerProfile
    value_map: ValueMap
    fit_evaluation: str = Field(
        ...,
        description="Pain RelieversとPain、Gain CreatorsとGainが論理的にFitしているかの検証結果",
    )
