"""
Defines the Sitemap and User Story domain models.
"""

from pydantic import BaseModel, ConfigDict, Field


class Route(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str = Field(..., description="URLパス (例: /, /dashboard, /login)", min_length=1)
    name: str = Field(..., description="ページ名", min_length=1)
    purpose: str = Field(..., description="このページの目的", min_length=5)
    is_protected: bool = Field(..., description="認証が必要なページかどうか")


class UserStory(BaseModel):
    model_config = ConfigDict(extra="forbid")
    as_a: str = Field(..., description="誰として(Persona)", min_length=1)
    i_want_to: str = Field(..., description="何をしたいか(Action)", min_length=1)
    so_that: str = Field(..., description="なぜなら〜を達成したいから(Goal/Value)", min_length=1)
    acceptance_criteria: list[str] = Field(
        ..., description="このストーリーが満たされたとする受け入れ条件", min_length=1
    )
    target_route: str = Field(..., description="このアクションを主に行うURLパス", min_length=1)


class SitemapAndStory(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sitemap: list[Route] = Field(
        ..., description="アプリケーション全体のURL・ルーティング構成", min_length=1
    )
    core_story: UserStory = Field(..., description="MVPとして検証すべき最重要な単一のストーリー")
