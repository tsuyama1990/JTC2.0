from pydantic import BaseModel, ConfigDict, Field

from src.core.config import get_settings


class MetricTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_name: str = Field(..., min_length=get_settings().validation.min_content_length)
    target_value: float = Field(...)
    measurement_method: str = Field(..., min_length=get_settings().validation.min_title_length)


class ExperimentPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    riskiest_assumption: str = Field(..., min_length=get_settings().validation.min_title_length)
    experiment_type: str = Field(..., min_length=get_settings().validation.min_content_length)
    acquisition_channel: str = Field(..., min_length=get_settings().validation.min_content_length)
    aarrr_metrics: list[MetricTarget] = Field(..., min_length=1)
    pivot_conditions: str = Field(..., min_length=get_settings().validation.min_title_length)
