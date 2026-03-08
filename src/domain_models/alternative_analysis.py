"""
Alternative Analysis models.
"""

from pydantic import BaseModel, ConfigDict, Field

from src.core.config import get_settings


class AlternativeTool(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="Name of the alternative tool (e.g., Excel, manual work, existing SaaS)",
    )
    financial_cost: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="Financial cost",
    )
    time_cost: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="Time cost",
    )
    ux_friction: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="The biggest stress/friction the user feels",
    )


class AlternativeAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_alternatives: list[AlternativeTool] = Field(
        ...,
        min_length=get_settings().validation.min_list_length,
    )
    switching_cost: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="Cost and effort incurred when the user switches",
    )
    ten_x_value: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="10x value of the alternative (UVP) that overwhelmingly surpasses the switching cost",
    )
