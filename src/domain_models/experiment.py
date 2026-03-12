"""
Defines the Experiment Plan domain models.
"""

from pydantic import BaseModel, ConfigDict, Field


class MetricTarget(BaseModel):
    model_config = ConfigDict(extra="forbid")
    metric_name: str = Field(
        ...,
        description="指標名(例: Day7 Retention)",
        min_length=1,
    )
    target_value: str = Field(
        ...,
        description="PMF達成とみなす目標値(例: 40%以上)",
        min_length=1,
    )
    measurement_method: str = Field(
        ..., description="計測方法", min_length=1
    )


class ExperimentPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    riskiest_assumption: str = Field(
        ...,
        description="今回検証する最もリスクの高い前提条件",
        min_length=3,
    )
    experiment_type: str = Field(
        ...,
        description="MVPの型(例: LP、コンシェルジュ、Wizard of Oz)",
        min_length=1,
    )
    acquisition_channel: str = Field(
        ...,
        description="初期の100人をどこから連れてくるか",
        min_length=1,
    )
    aarrr_metrics: list[MetricTarget] = Field(
        ...,
        description="AARRRフレームワークに基づく追跡指標",
        min_length=1,
    )
    pivot_condition: str = Field(
        ...,
        description="どのような結果になれば即撤退(ピボット)すべきか",
        min_length=3,
    )
