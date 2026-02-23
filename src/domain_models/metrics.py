from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.core.constants import DESC_METRICS_AARRR, DESC_METRICS_CUSTOM, VAL_MAX_CUSTOM_METRICS


class AARRR(BaseModel):
    model_config = ConfigDict(extra="forbid")

    acquisition: float = Field(0.0, ge=0.0, description="Acquisition metric")
    activation: float = Field(0.0, ge=0.0, description="Activation metric")
    retention: float = Field(0.0, ge=0.0, le=100.0, description="Retention percentage")
    revenue: float = Field(0.0, ge=0.0, description="Revenue metric")
    referral: float = Field(0.0, ge=0.0, description="Referral metric")


class Metrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    aarrr: AARRR = Field(default_factory=AARRR, description=DESC_METRICS_AARRR)
    custom_metrics: dict[str, float] = Field(
        default_factory=dict, description=DESC_METRICS_CUSTOM
    )

    @field_validator("custom_metrics")
    @classmethod
    def validate_custom_metrics_limit(cls, v: dict[str, float]) -> dict[str, float]:
        """Ensure the number of custom metrics does not exceed the limit."""
        if len(v) > VAL_MAX_CUSTOM_METRICS:
            msg = f"Too many custom metrics. Limit is {VAL_MAX_CUSTOM_METRICS}"
            raise ValueError(msg)
        return v
