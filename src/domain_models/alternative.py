"""
Defines the Alternative Analysis domain models.
"""

from pydantic import BaseModel, ConfigDict, Field

from src.core.config import get_settings


class AlternativeTool(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(
        ...,
        description="代替品の名前(例: Excel、手作業、既存SaaS)",
        min_length=get_settings().validation.min_list_length,
    )
    financial_cost: str = Field(
        ..., description="金銭的コスト", min_length=get_settings().validation.min_list_length
    )
    time_cost: str = Field(
        ..., description="時間的コスト", min_length=get_settings().validation.min_list_length
    )
    ux_friction: str = Field(
        ...,
        description="ユーザーが感じる最大のストレス・摩擦",
        min_length=get_settings().validation.min_list_length,
    )


class AlternativeAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_alternatives: list[AlternativeTool] = Field(
        ..., description="現状の代替手段", min_length=get_settings().validation.min_list_length
    )
    switching_cost: str = Field(
        ...,
        description="ユーザーが乗り換える際に発生するコストや手間",
        min_length=get_settings().validation.min_content_length,
    )
    ten_x_value: str = Field(
        ...,
        description="スイッチングコストを圧倒する、代替品の10倍の価値(UVP)",
        min_length=get_settings().validation.min_content_length,
    )
