"""
Defines the Agent Prompt Spec domain models.
"""

from pydantic import BaseModel, ConfigDict, Field

from src.core.config import get_settings

from .sitemap import UserStory


class StateMachine(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: str = Field(
        ...,
        description="データ正常時の完全なレイアウト",
        min_length=get_settings().validation.min_list_length,
    )
    loading: str = Field(
        ...,
        description="Skeletonコンポーネントを用いた待機UI",
        min_length=get_settings().validation.min_list_length,
    )
    error: str = Field(
        ...,
        description="フォールバックUIとRetryボタンの配置",
        min_length=get_settings().validation.min_list_length,
    )
    empty: str = Field(
        ...,
        description="データ0件時のCTAを含むEmpty State",
        min_length=get_settings().validation.min_list_length,
    )


class AgentPromptSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sitemap: str = Field(
        ...,
        description="アプリ全体のルーティングと情報アーキテクチャ",
        min_length=get_settings().validation.min_list_length,
    )
    routing_and_constraints: str = Field(
        ...,
        description="SSR/Client Componentの境界、UIライブラリの指定",
        min_length=get_settings().validation.min_list_length,
    )
    core_user_story: UserStory = Field(..., description="MVPのコアイーストーリー")
    state_machine: StateMachine = Field(..., description="状態ごとのUIマッピング")
    validation_rules: str = Field(
        ...,
        description="Zodスキーマやエッジケースの要件",
        min_length=get_settings().validation.min_list_length,
    )
    mermaid_flowchart: str = Field(
        ...,
        description="Mermaid構文による状態遷移・データフロー図",
        min_length=get_settings().validation.min_list_length,
    )
