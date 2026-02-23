from pydantic import BaseModel, ConfigDict, Field


class AARRR(BaseModel):
    model_config = ConfigDict(extra="forbid")

    acquisition: float = Field(0.0, description="Acquisition metric")
    activation: float = Field(0.0, description="Activation metric")
    retention: float = Field(0.0, description="Retention metric")
    revenue: float = Field(0.0, description="Revenue metric")
    referral: float = Field(0.0, description="Referral metric")


class Metrics(BaseModel):
    model_config = ConfigDict(extra="forbid")

    aarrr: AARRR = Field(default_factory=AARRR)
    custom_metrics: dict[str, float] = Field(default_factory=dict)
