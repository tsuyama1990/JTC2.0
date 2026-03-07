from pydantic import BaseModel, ConfigDict, Field


class AlternativeTool(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=2)
    financial_cost: str = Field(..., min_length=1)
    time_cost: str = Field(..., min_length=1)
    ux_friction: str = Field(..., min_length=1)


class AlternativeAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_alternatives: list[AlternativeTool] = Field(..., min_length=1)
    switching_cost: str = Field(..., min_length=10)
    ten_x_value: str = Field(..., min_length=10)
