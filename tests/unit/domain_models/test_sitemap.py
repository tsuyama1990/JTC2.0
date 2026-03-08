import pytest
from pydantic import ValidationError

from src.domain_models.sitemap import Route, SitemapAndStory, UserStory


def test_route_valid() -> None:
    route = Route(
        path="/dashboard",
        name="Main Dashboard",
        purpose="Shows the high-level metrics and current status of tasks.",
        is_protected=True,
    )
    assert route.path == "/dashboard"


def test_route_invalid() -> None:
    with pytest.raises(ValidationError):
        Route(
            path="",  # min_length=1
            name="Main Dashboard",
            purpose="Short",  # min_length=10
            is_protected=True,
        )


def test_user_story_valid() -> None:
    story = UserStory(
        as_a="Data Analyst",
        i_want_to="upload my Excel sheet and automatically classify the data",
        so_that="I can save 2 hours a day and avoid manual entry errors",
        acceptance_criteria=[
            "Given I am on the dashboard, When I upload a file, Then the data is classified",
            "The data classification accuracy must be >90%",
        ],
        target_route="/upload",
    )
    assert story.as_a == "Data Analyst"


def test_user_story_invalid() -> None:
    with pytest.raises(ValidationError):
        UserStory(
            as_a="Data Analyst",
            i_want_to="upload my Excel sheet and automatically classify the data",
            so_that="Short",  # min_length=10
            acceptance_criteria=[],  # min_length validation from settings
            target_route="/upload",
        )


def test_sitemap_and_story_valid() -> None:
    route = Route(
        path="/dashboard",
        name="Main Dashboard",
        purpose="Shows the high-level metrics and current status of tasks.",
        is_protected=True,
    )
    story = UserStory(
        as_a="Data Analyst",
        i_want_to="upload my Excel sheet and automatically classify the data",
        so_that="I can save 2 hours a day and avoid manual entry errors",
        acceptance_criteria=["Criterion 1"],
        target_route="/upload",
    )
    sitemap_story = SitemapAndStory(
        sitemap=[route],
        core_story=story,
    )
    assert sitemap_story.sitemap[0].name == "Main Dashboard"


def test_sitemap_and_story_invalid() -> None:
    story = UserStory(
        as_a="Data Analyst",
        i_want_to="upload my Excel sheet and automatically classify the data",
        so_that="I can save 2 hours a day and avoid manual entry errors",
        acceptance_criteria=["Criterion 1"],
        target_route="/upload",
    )
    with pytest.raises(ValidationError):
        SitemapAndStory(
            sitemap=[],  # invalid length
            core_story=story,
        )
