"""
Alternative Analysis models.
"""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.core.config import get_settings


class AlternativeTool(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ...,
        description="Name of the alternative tool (e.g., Excel, manual work, existing SaaS)",
    )
    financial_cost: str = Field(
        ...,
        description="Financial cost",
    )
    time_cost: str = Field(
        ...,
        description="Time cost",
    )
    ux_friction: str = Field(
        ...,
        description="The biggest stress/friction the user feels",
    )

    @model_validator(mode="after")
    def validate_lengths(self) -> Self:
        settings = get_settings()
        for field in ["name", "financial_cost", "time_cost", "ux_friction"]:
            val = getattr(self, field)
            if isinstance(val, str) and len(val) < settings.validation.min_content_length:
                msg = (
                    f"{field} must be at least {settings.validation.min_content_length} characters"
                )
                raise ValueError(msg)
        return self


class AlternativeAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_alternatives: list[AlternativeTool] = Field(...)
    switching_cost: str = Field(
        ...,
        description="Cost and effort incurred when the user switches",
    )
    ten_x_value: str = Field(
        ...,
        description="10x value of the alternative (UVP) that overwhelmingly surpasses the switching cost",
    )

    @model_validator(mode="after")
    def validate_lengths(self) -> Self:
        settings = get_settings()
        for field in ["switching_cost", "ten_x_value"]:
            val = getattr(self, field)
            if isinstance(val, str) and len(val) < settings.validation.min_content_length:
                msg = (
                    f"{field} must be at least {settings.validation.min_content_length} characters"
                )
                raise ValueError(msg)

        if len(self.current_alternatives) < settings.validation.min_list_length:
            msg = f"current_alternatives must contain at least {settings.validation.min_list_length} items"
            raise ValueError(msg)

        return self
