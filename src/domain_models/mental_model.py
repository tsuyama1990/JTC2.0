from pydantic import BaseModel, ConfigDict, Field

from src.core.config import get_settings


class MentalTower(BaseModel):
    """
    Represents a 'Tower of Thought' (beliefs/values) behind user actions.
    """

    model_config = ConfigDict(extra="forbid")

    belief: str = Field(
        ...,
        description="A core belief or value",
        min_length=10,
        max_length=200,
    )
    cognitive_tasks: list[str] = Field(
        ...,
        description="List of cognitive tasks associated with this belief",
        min_length=get_settings().validation.min_list_length,
        max_length=get_settings().validation.max_list_length,
    )


class MentalModelDiagram(BaseModel):
    """
    Mental Model Diagram. Visualises the 'Towers of Thought' and aligns
    features to them.
    """

    model_config = ConfigDict(extra="forbid")

    towers: list[MentalTower] = Field(
        ...,
        description="List of 'Towers of Thought'",
        min_length=get_settings().validation.min_list_length,
        max_length=get_settings().validation.max_list_length,
    )
    feature_alignment: str = Field(
        ...,
        description="A string mapping proposed features to these towers",
        min_length=10,
        max_length=1000,
    )
