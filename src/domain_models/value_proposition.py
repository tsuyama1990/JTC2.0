"""
Defines the Value Proposition Canvas domain models.
"""

from pydantic import BaseModel, ConfigDict, Field

from src.core.config import get_settings


class CustomerProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_jobs: list[str] = Field(
        ...,
        description="顧客が片付けたい用事・社会的/感情的タスク",
        min_length=get_settings().validation.min_list_length,
    )
    pains: list[str] = Field(
        ...,
        description="ジョブの実行を妨げるリスクやネガティブな感情",
        min_length=get_settings().validation.min_list_length,
    )
    gains: list[str] = Field(
        ...,
        description="ジョブの実行によって得たい恩恵や期待",
        min_length=get_settings().validation.min_list_length,
    )


class ValueMap(BaseModel):
    model_config = ConfigDict(extra="forbid")
    products_and_services: list[str] = Field(
        ...,
        description="提供する主要な製品・サービスのリスト",
        min_length=get_settings().validation.min_list_length,
    )
    pain_relievers: list[str] = Field(
        ...,
        description="顧客のPainを具体的にどう取り除くか",
        min_length=get_settings().validation.min_list_length,
    )
    gain_creators: list[str] = Field(
        ...,
        description="顧客のGainを具体的にどう創出するか",
        min_length=get_settings().validation.min_list_length,
    )


class ValuePropositionCanvas(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_profile: CustomerProfile
    value_map: ValueMap
    fit_evaluation: str = Field(
        ...,
        description="Pain RelieversとPain、Gain CreatorsとGainが論理的にFitしているかの検証結果",
        min_length=get_settings().validation.min_content_length,
    )
