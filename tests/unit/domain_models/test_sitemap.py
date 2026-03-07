import pytest
from pydantic import ValidationError

from src.domain_models.sitemap import Route, SitemapAndStory, UserStory


def test_route() -> None:
    route = Route(path="/home", name="Home", purpose="Landing page", is_protected=False)
    assert route.path == "/home"

    with pytest.raises(ValidationError):
        Route(path="", name="", purpose="Hi", is_protected=False)


def test_user_story() -> None:
    story = UserStory(
        as_a="User",
        i_want_to="Login to my account",
        so_that="I can see my dashboard",
        acceptance_criteria=[
            "Must have valid credentials",
            "Must show error message",
            "Must redirect on success",
        ],
        target_route="/login",
    )
    assert story.as_a == "User"

    with pytest.raises(ValidationError):
        UserStory(as_a="U", i_want_to="Log", so_that="See", acceptance_criteria=[], target_route="")


def test_sitemap_and_story() -> None:
    route = Route(path="/home", name="Home", purpose="Landing page", is_protected=False)
    route2 = Route(path="/login", name="Login", purpose="Authentication", is_protected=False)
    route3 = Route(path="/dash", name="Dash", purpose="Dashboard view", is_protected=True)
    story = UserStory(
        as_a="User",
        i_want_to="Login to my account",
        so_that="I can see my dashboard",
        acceptance_criteria=[
            "Must have valid credentials",
            "Must show error message",
            "Must redirect on success",
        ],
        target_route="/login",
    )
    sitemap = SitemapAndStory(routes=[route, route2, route3], core_story=story)
    assert len(sitemap.routes) == 3

    with pytest.raises(ValidationError):
        SitemapAndStory(routes=[], core_story=story)
