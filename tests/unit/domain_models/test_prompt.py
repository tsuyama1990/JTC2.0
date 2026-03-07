import pytest
from pydantic import ValidationError

from src.domain_models.prompt import AgentPromptSpec, StateMachine
from src.domain_models.sitemap import Route, SitemapAndStory, UserStory


def test_state_machine() -> None:
    sm = StateMachine(
        success_state="Show dashboard",
        loading_state="Show spinner",
        error_state="Show error message",
        empty_state="Show welcome guide",
    )
    assert sm.success_state == "Show dashboard"

    with pytest.raises(ValidationError):
        StateMachine(success_state="Hi", loading_state="Wait", error_state="Err", empty_state="Emp")


def test_agent_prompt_spec() -> None:
    route1 = Route(path="/home", name="Home", purpose="Landing page", is_protected=False)
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
    sitemap = SitemapAndStory(routes=[route1, route2, route3], core_story=story)
    sm = StateMachine(
        success_state="Show dashboard",
        loading_state="Show spinner",
        error_state="Show error message",
        empty_state="Show welcome guide",
    )
    spec = AgentPromptSpec(
        sitemap=sitemap,
        routing_constraints=[
            "Must be logged in to see dashboard",
            "Must not be logged in to see login",
            "Must be logged in to see account",
        ],
        core_user_story=story,
        state_machine=sm,
        validation_rules=[
            "Password must be at least 8 characters",
            "Email must be valid format",
            "Username must be unique",
        ],
        mermaid_flowchart="graph TD; A-->B;",
    )
    assert len(spec.routing_constraints) == 3

    with pytest.raises(ValidationError):
        AgentPromptSpec(
            sitemap=sitemap,
            routing_constraints=[],
            core_user_story=story,
            state_machine=sm,
            validation_rules=[],
            mermaid_flowchart="graph TD;",
        )
