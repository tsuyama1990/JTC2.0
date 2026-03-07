from pydantic import BaseModel, ConfigDict, Field


class MetricTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_name: str = Field(..., min_length=2)
    target_value: float = Field(...)
    measurement_method: str = Field(..., min_length=5)


class ExperimentPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    riskiest_assumption: str = Field(..., min_length=10)
    experiment_type: str = Field(..., min_length=3)
    acquisition_channel: str = Field(..., min_length=3)
    aarrr_metrics: list[MetricTarget] = Field(..., min_length=1)
    pivot_conditions: str = Field(..., min_length=10)
