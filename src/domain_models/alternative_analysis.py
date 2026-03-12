from pydantic import BaseModel, ConfigDict, Field


class AlternativeTool(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., description="代替品の名前（例：Excel、手作業、既存SaaS）")
    financial_cost: str = Field(..., description="金銭的コスト")
    time_cost: str = Field(..., description="時間的コスト")
    ux_friction: str = Field(..., description="ユーザーが感じる最大のストレス・摩擦")


class AlternativeAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_alternatives: list[AlternativeTool]
    switching_cost: str = Field(..., description="ユーザーが乗り換える際に発生するコストや手間")
    ten_x_value: str = Field(
        ..., description="スイッチングコストを圧倒する、代替品の10倍の価値（UVP）"
    )
