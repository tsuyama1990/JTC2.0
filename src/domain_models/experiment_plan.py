"""
Experiment Plan models.
"""

from pydantic import BaseModel, ConfigDict, Field

from src.core.config import get_settings


class MetricTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_name: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="Metric name (e.g., Day7 Retention)",
    )
    target_value: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="Target value considered as achieving PMF (e.g., 40% or more)",
    )
    measurement_method: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="Measurement method",
    )


class ExperimentPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    riskiest_assumption: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="The riskiest assumption to be tested this time",
    )
    experiment_type: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="Type of MVP (e.g., LP, Concierge, Wizard of Oz)",
    )
    acquisition_channel: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="Where to bring the initial 100 users from",
    )
    aarrr_metrics: list[MetricTarget] = Field(
        ...,
        min_length=get_settings().validation.min_list_length,
        description="Tracking metrics based on the AARRR framework",
    )
    pivot_condition: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="What results should trigger an immediate withdrawal (pivot)",
    )
