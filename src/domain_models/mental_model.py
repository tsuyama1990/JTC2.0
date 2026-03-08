"""
Mental Model diagram for understanding user psychology.
"""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.core.config import get_settings


class MentalTower(BaseModel):
    model_config = ConfigDict(extra="forbid")

    belief: str = Field(
        ...,
        description="The underlying belief or value of the user (e.g., 'I do not want to waste time')",
    )
    cognitive_tasks: list[str] = Field(
        ...,
        description="Tasks and judgments performed in the mind based on that belief",
    )

    @model_validator(mode="after")
    def validate_lengths(self) -> Self:
        settings = get_settings()
        if len(self.belief) < settings.validation.min_content_length:
            msg = f"belief must be at least {settings.validation.min_content_length} characters"
            raise ValueError(msg)

        if len(self.cognitive_tasks) < settings.validation.min_list_length:
            msg = f"cognitive_tasks must contain at least {settings.validation.min_list_length} items"
            raise ValueError(msg)

        return self


class MentalModelDiagram(BaseModel):
    model_config = ConfigDict(extra="forbid")

    towers: list[MentalTower] = Field(
        ...,
        description="Multiple towers of thought that constitute the user's mental space",
    )
    feature_alignment: str = Field(
        ...,
        description="Mapping of how the provided features align with and support the defined thought towers",
    )

    @model_validator(mode="after")
    def validate_lengths(self) -> Self:
        settings = get_settings()
        if len(self.feature_alignment) < settings.validation.min_content_length:
            msg = f"feature_alignment must be at least {settings.validation.min_content_length} characters"
            raise ValueError(msg)

        if len(self.towers) < settings.validation.min_list_length:
            msg = f"towers must contain at least {settings.validation.min_list_length} items"
            raise ValueError(msg)

        return self
