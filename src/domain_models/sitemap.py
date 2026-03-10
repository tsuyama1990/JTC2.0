"""
Sitemap and User Story models.
"""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
        description="Purpose of this page",
    )
    is_protected: bool = Field(
        ...,
        description="Whether the page requires authentication",
    )

    @model_validator(mode="after")
    def validate_lengths(self) -> Self:

        if len(self.purpose) < 10:
            msg = f"purpose must be at least {10} characters"
            raise ValueError(msg)
        return self


class UserStory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    as_a: str = Field(
        ...,
        description="As a (Persona)",
    )
    i_want_to: str = Field(
        ...,
        description="I want to (Action)",
    )
    so_that: str = Field(
        ...,
        description="So that (Goal/Value)",
    )
    acceptance_criteria: list[str] = Field(
        ...,
        description="Acceptance criteria for this story to be considered satisfied",
    )
    target_route: str = Field(
        ...,
        min_length=1,
        description="URL path where this action primarily occurs",
    )

    @model_validator(mode="after")
    def validate_lengths(self) -> Self:

        for field in ["as_a", "i_want_to", "so_that"]:
            val = getattr(self, field)
            if isinstance(val, str) and len(val) < 10:
                msg = (
                    f"{field} must be at least {10} characters"
                )
                raise ValueError(msg)

        if len(self.acceptance_criteria) < 1:
            msg = f"acceptance_criteria must contain at least {1} items"
            raise ValueError(msg)

        return self


class SitemapAndStory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sitemap: list[Route] = Field(
        ...,
        description="Overall URL and routing structure of the application",
    )
    core_story: UserStory = Field(
        ...,
        description="The single most important story to be validated as an MVP",
    )

    @model_validator(mode="after")
    def validate_lengths(self) -> Self:

        if len(self.sitemap) < 1:
            msg = f"sitemap must contain at least {1} items"
            raise ValueError(msg)
        return self
