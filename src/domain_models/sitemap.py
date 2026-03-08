"""
Sitemap and User Story models.
"""

from pydantic import BaseModel, ConfigDict, Field

from src.core.config import get_settings


class Route(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(
        ...,
        min_length=1,
        description="URL path (e.g., /, /dashboard, /login)",
    )
    name: str = Field(
        ...,
        min_length=1,
        description="Page name",
    )
    purpose: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="Purpose of this page",
    )
    is_protected: bool = Field(
        ...,
        description="Whether the page requires authentication",
    )


class UserStory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    as_a: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="As a (Persona)",
    )
    i_want_to: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="I want to (Action)",
    )
    so_that: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="So that (Goal/Value)",
    )
    acceptance_criteria: list[str] = Field(
        ...,
        min_length=get_settings().validation.min_list_length,
        description="Acceptance criteria for this story to be considered satisfied",
    )
    target_route: str = Field(
        ...,
        min_length=1,
        description="URL path where this action primarily occurs",
    )


class SitemapAndStory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sitemap: list[Route] = Field(
        ...,
        min_length=get_settings().validation.min_list_length,
        description="Overall URL and routing structure of the application",
    )
    core_story: UserStory = Field(
        ...,
        description="The single most important story to be validated as an MVP",
    )
