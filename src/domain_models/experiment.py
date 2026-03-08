from pydantic import BaseModel, ConfigDict, Field


class MetricTarget(BaseModel):
    """
    Defines 'what and how to measure' using the generated MVP.
    """

    model_config = ConfigDict(extra="forbid")

    metric_name: str = Field(
        ...,
        description="The name of the metric to track",
        min_length=1,
        max_length=50,
    )
    target_value: float = Field(
        ...,
        description="The target value for the metric",
    )
    measurement_method: str = Field(
        ...,
        description="The method used to measure this metric",
        min_length=10,
        max_length=200,
    )


class ExperimentPlan(BaseModel):
    """
    Experiment Plan Model. AARRR-based KPI tree defining the experiment.
    """

    model_config = ConfigDict(extra="forbid")

    riskiest_assumption: str = Field(
        ...,
        description="The most critical assumption being tested",
        min_length=10,
        max_length=200,
    )
    experiment_type: str = Field(
        ...,
        description="The type of experiment (e.g. Concierge, Landing Page)",
        min_length=1,
        max_length=50,
    )
    acquisition_channel: str = Field(
        ...,
        description="The channel used to acquire users",
        min_length=1,
        max_length=50,
    )
    aarrr_metrics: list[MetricTarget] = Field(
        ...,
        description="List of AARRR metrics being tracked",
        min_length=5,
        max_length=5,
    )
    pivot_condition: str = Field(
        ...,
        description="The condition under which the team should pivot",
        min_length=10,
        max_length=200,
    )
