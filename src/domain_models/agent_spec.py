"""
Defines the Agent Prompt Spec domain models.
"""

from pydantic import BaseModel, ConfigDict, Field

from .sitemap import UserStory


class StateMachine(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: str = Field(..., description="データ正常時の完全なレイアウト", min_length=1)
    loading: str = Field(..., description="Skeletonコンポーネントを用いた待機UI", min_length=1)
    error: str = Field(..., description="フォールバックUIとRetryボタンの配置", min_length=1)
    empty: str = Field(..., description="データ0件時のCTAを含むEmpty State", min_length=1)


class AgentPromptSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sitemap: str = Field(
        ..., description="アプリ全体のルーティングと情報アーキテクチャ", min_length=1
    )
    routing_and_constraints: str = Field(
        ..., description="SSR/Client Componentの境界、UIライブラリの指定", min_length=1
    )
    core_user_story: UserStory = Field(..., description="MVPのコアイーストーリー")
    state_machine: StateMachine = Field(..., description="状態ごとのUIマッピング")
    validation_rules: str = Field(..., description="Zodスキーマやエッジケースの要件", min_length=1)
    mermaid_flowchart: str = Field(
        ..., description="Mermaid構文による状態遷移・データフロー図", min_length=1
    )
