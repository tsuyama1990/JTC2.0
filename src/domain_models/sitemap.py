from pydantic import BaseModel, ConfigDict, Field

from src.core.config import get_settings


class Route(BaseModel):
    """
    Represents a URL structure or page transition.
    """

    model_config = ConfigDict(extra="forbid")

    path: str = Field(
        ...,
        description="The URL path",
        min_length=1,
        max_length=100,
    )
    name: str = Field(
        ...,
        description="Name of the route",
        min_length=1,
        max_length=50,
    )
    purpose: str = Field(
        ...,
        description="The purpose of this route",
        min_length=10,
        max_length=200,
    )
    is_protected: bool = Field(
        ...,
        description="Whether this route requires authentication",
    )


class UserStory(BaseModel):
    """
    Represents a user story extracted from the touchpoint with the strongest pain.
    """

    model_config = ConfigDict(extra="forbid")

    as_a: str = Field(
        ...,
        description="Role or persona (As a...)",
        min_length=1,
        max_length=50,
    )
    i_want_to: str = Field(
        ...,
        description="Goal (I want to...)",
        min_length=10,
        max_length=200,
    )
    so_that: str = Field(
        ...,
        description="Benefit (So that...)",
        min_length=10,
        max_length=200,
    )
    acceptance_criteria: list[str] = Field(
        ...,
        description="List of acceptance criteria for this story",
        min_length=get_settings().validation.min_list_length,
        max_length=get_settings().validation.max_list_length,
    )
    target_route: str = Field(
        ...,
        description="The target Route path this story applies to",
        min_length=1,
        max_length=100,
    )


class SitemapAndStory(BaseModel):
    """
    Sitemap & User Story Model. Defines URL structure and the core user story.
    """

    model_config = ConfigDict(extra="forbid")

    sitemap: list[Route] = Field(
        ...,
        description="List of routes defining the overall structure",
        min_length=get_settings().validation.min_list_length,
        max_length=get_settings().validation.max_list_length,
    )
    core_story: UserStory = Field(
        ...,
        description="The core user story representing the strongest pain",
    )
