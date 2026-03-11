from pydantic import BaseModel, ConfigDict, Field


class Route(BaseModel):
    path: str = Field(..., description="URLパス (例: /, /dashboard, /login)")
    name: str = Field(..., description="ページ名")
    purpose: str = Field(..., description="このページの目的")
    is_protected: bool = Field(..., description="認証が必要なページかどうか")


class UserStory(BaseModel):
    model_config = ConfigDict(extra="forbid")
    as_a: str = Field(..., description="誰として（Persona）")
    i_want_to: str = Field(..., description="何をしたいか（Action）")
    so_that: str = Field(..., description="なぜなら〜を達成したいから（Goal/Value）")
    acceptance_criteria: list[str] = Field(
        ..., description="このストーリーが満たされたとする受け入れ条件"
    )
    target_route: str = Field(..., description="このアクションを主に行うURLパス")


class SitemapAndStory(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sitemap: list[Route] = Field(..., description="アプリケーション全体のURL・ルーティング構成")
    core_story: UserStory = Field(..., description="MVPとして検証すべき最重要な単一のストーリー")
