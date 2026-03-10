"""
Experiment Plan models.
"""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.core.config import SettingsFactory


class MetricTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")

    metric_name: str = Field(
        ...,
        description="Metric name (e.g., Day7 Retention)",
    )
    target_value: str = Field(
        ...,
        description="Target value considered as achieving PMF (e.g., 40% or more)",
    )
    measurement_method: str = Field(
        ...,
        description="Measurement method",
    )

    @model_validator(mode="after")
    def validate_lengths(self) -> Self:
        settings = SettingsFactory().build()
        for field in ["metric_name", "target_value", "measurement_method"]:
            val = getattr(self, field)
            if isinstance(val, str) and len(val) < settings.validation.min_content_length:
                msg = (
                    f"{field} must be at least {settings.validation.min_content_length} characters"
                )
                raise ValueError(msg)
        return self


class ExperimentPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    riskiest_assumption: str = Field(
        ...,
        description="The riskiest assumption to be tested this time",
    )
    experiment_type: str = Field(
        ...,
        description="Type of MVP (e.g., LP, Concierge, Wizard of Oz)",
    )
    acquisition_channel: str = Field(
        ...,
        description="Where to bring the initial 100 users from",
    )
    aarrr_metrics: list[MetricTarget] = Field(
        ...,
        description="Tracking metrics based on the AARRR framework",
    )
    pivot_condition: str = Field(
        ...,
        description="What results should trigger an immediate withdrawal (pivot)",
    )

    @model_validator(mode="after")
    def validate_lengths(self) -> Self:
        settings = SettingsFactory().build()
        for field in [
            "riskiest_assumption",
            "experiment_type",
            "acquisition_channel",
            "pivot_condition",
        ]:
            val = getattr(self, field)
            if isinstance(val, str) and len(val) < settings.validation.min_content_length:
                msg = (
                    f"{field} must be at least {settings.validation.min_content_length} characters"
                )
                raise ValueError(msg)

        if len(self.aarrr_metrics) < settings.validation.min_list_length:
            msg = f"aarrr_metrics must contain at least {settings.validation.min_list_length} items"
            raise ValueError(msg)

        return self
