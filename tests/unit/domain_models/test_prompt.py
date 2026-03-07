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
    route = Route(path="/home", name="Home", purpose="Landing page", is_protected=False)
    story = UserStory(
        as_a="User",
        i_want_to="Login to my account",
        so_that="I can see my dashboard",
        acceptance_criteria=["Must have valid credentials"],
        target_route="/login",
    )
    sitemap = SitemapAndStory(routes=[route], core_story=story)
    sm = StateMachine(
        success_state="Show dashboard",
        loading_state="Show spinner",
        error_state="Show error message",
        empty_state="Show welcome guide",
    )
    spec = AgentPromptSpec(
        sitemap=sitemap,
        routing_constraints=["Must be logged in to see dashboard"],
        core_user_story=story,
        state_machine=sm,
        validation_rules=["Password must be at least 8 characters"],
        mermaid_flowchart="graph TD; A-->B;",
    )
    assert len(spec.routing_constraints) == 1

    with pytest.raises(ValidationError):
        AgentPromptSpec(
            sitemap=sitemap,
            routing_constraints=[],
            core_user_story=story,
            state_machine=sm,
            validation_rules=[],
            mermaid_flowchart="graph TD;",
        )
