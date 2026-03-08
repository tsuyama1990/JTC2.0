from pydantic import BaseModel, ConfigDict, Field

from src.core.config import get_settings


class AlternativeTool(BaseModel):
    """
    Represents an alternative tool or solution currently used by the persona.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Name of the alternative tool", min_length=1, max_length=50)
    financial_cost: str = Field(
        ...,
        description="Description of the financial cost associated",
        min_length=1,
        max_length=100,
    )
    time_cost: str = Field(
        ..., description="Description of the time cost associated", min_length=1, max_length=100
    )
    ux_friction: str = Field(
        ..., description="Description of the UX friction experienced", min_length=1, max_length=200
    )


class AlternativeAnalysis(BaseModel):
    """
    Alternative Analysis Model. Identifies current alternative solutions and
    deduces a '10x Value' that outweighs switching costs.
    """

    model_config = ConfigDict(extra="forbid")

    current_alternatives: list[AlternativeTool] = Field(
        ...,
        description="List of alternative tools currently used",
        min_length=get_settings().validation.min_list_length,
        max_length=get_settings().validation.max_list_length,
    )
    switching_cost: str = Field(
        ...,
        description="The cost of switching from current alternatives",
        min_length=10,
        max_length=500,
    )
    ten_x_value: str = Field(
        ...,
        description="The deduced '10x Value' that outweighs the switching costs",
        min_length=10,
        max_length=500,
    )
