"""
Mental Model diagram for understanding user psychology.
"""

from pydantic import BaseModel, ConfigDict, Field

from src.core.config import get_settings


class MentalTower(BaseModel):
    model_config = ConfigDict(extra="forbid")

    belief: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="The underlying belief or value of the user (e.g., 'I do not want to waste time')",
    )
    cognitive_tasks: list[str] = Field(
        ...,
        min_length=get_settings().validation.min_list_length,
        description="Tasks and judgments performed in the mind based on that belief",
    )


class MentalModelDiagram(BaseModel):
    model_config = ConfigDict(extra="forbid")

    towers: list[MentalTower] = Field(
        ...,
        min_length=get_settings().validation.min_list_length,
        description="Multiple towers of thought that constitute the user's mental space",
    )
    feature_alignment: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="Mapping of how the provided features align with and support the defined thought towers",
    )
