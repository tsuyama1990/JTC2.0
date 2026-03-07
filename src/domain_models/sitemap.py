from pydantic import BaseModel, ConfigDict, Field


class Route(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    purpose: str = Field(..., min_length=5)
    is_protected: bool


class UserStory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    as_a: str = Field(..., min_length=2)
    i_want_to: str = Field(..., min_length=5)
    so_that: str = Field(..., min_length=5)
    acceptance_criteria: list[str] = Field(..., min_length=1)
    target_route: str = Field(..., min_length=1)


class SitemapAndStory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    routes: list[Route] = Field(..., min_length=1)
    core_story: UserStory
