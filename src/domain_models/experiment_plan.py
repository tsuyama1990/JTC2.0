from pydantic import BaseModel, ConfigDict, Field


class MetricTarget(BaseModel):
    metric_name: str = Field(..., description="指標名（例：Day7 Retention）")
    target_value: str = Field(..., description="PMF達成とみなす目標値（例：40%以上）")
    measurement_method: str = Field(..., description="計測方法")


class ExperimentPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    riskiest_assumption: str = Field(..., description="今回検証する最もリスクの高い前提条件")
    experiment_type: str = Field(..., description="MVPの型（例：LP、コンシェルジュ、Wizard of Oz）")
    acquisition_channel: str = Field(..., description="初期の100人をどこから連れてくるか")
    aarrr_metrics: list[MetricTarget] = Field(
        ..., description="AARRRフレームワークに基づく追跡指標"
    )
    pivot_condition: str = Field(
        ..., description="どのような結果になれば即撤退（ピボット）すべきか"
    )
