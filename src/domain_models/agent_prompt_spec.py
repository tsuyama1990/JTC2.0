from pydantic import BaseModel, ConfigDict, Field

from src.domain_models.sitemap_and_story import UserStory


class StateMachine(BaseModel):
    success: str = Field(..., description="データ正常時の完全なレイアウト")
    loading: str = Field(..., description="Skeletonコンポーネントを用いた待機UI")
    error: str = Field(..., description="フォールバックUIとRetryボタンの配置")
    empty: str = Field(..., description="データ0件時のCTAを含むEmpty State")


class AgentPromptSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sitemap: str = Field(..., description="アプリ全体のルーティングと情報アーキテクチャ")
    routing_and_constraints: str = Field(
        ..., description="SSR/Client Componentの境界、UIライブラリの指定"
    )
    core_user_story: UserStory
    state_machine: StateMachine
    validation_rules: str = Field(..., description="Zodスキーマやエッジケースの要件")
    mermaid_flowchart: str = Field(..., description="Mermaid構文による状態遷移・データフロー図")
