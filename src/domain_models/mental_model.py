"""
Mental Model diagram for understanding user psychology.
"""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
        if len(self.belief) < 10:
            msg = "belief must be at least 10 characters"
            raise ValueError(msg)

        if len(self.cognitive_tasks) < 1:
            msg = f"cognitive_tasks must contain at least {1} items"
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
        if len(self.feature_alignment) < 10:
            msg = "feature_alignment must be at least 10 characters"
            raise ValueError(msg)

        if len(self.towers) < 1:
            msg = f"towers must contain at least {1} items"
            raise ValueError(msg)

        return self
