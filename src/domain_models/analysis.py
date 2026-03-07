from pydantic import BaseModel, ConfigDict, Field

from src.core.config import get_settings


class AlternativeTool(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=get_settings().validation.min_content_length)
    financial_cost: str = Field(..., min_length=1)
    time_cost: str = Field(..., min_length=1)
    ux_friction: str = Field(..., min_length=1)


class AlternativeAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    current_alternatives: list[AlternativeTool] = Field(..., min_length=1)
    switching_cost: str = Field(..., min_length=get_settings().validation.min_title_length)
    ten_x_value: str = Field(..., min_length=get_settings().validation.min_title_length)
