import pytest
from pydantic import ValidationError

from src.domain_models.sitemap import Route, UserStory
from src.domain_models.spec import AgentPromptSpec, StateMachine


def test_state_machine_valid() -> None:
    sm = StateMachine(
        success="Displays a green checkmark and a button to proceed to dashboard.",
        loading="Shows a spinning wheel with 'processing your request...' text.",
        error="Displays a red banner with an actionable 'retry' button.",
        empty="Shows an illustration of an empty folder and a 'create new' button.",
    )
    assert "green checkmark" in sm.success


def test_state_machine_invalid() -> None:
    with pytest.raises(ValidationError):
        StateMachine(
            success="Short",  # min_length=10
            loading="Shows a spinning wheel with 'processing your request...' text.",
            error="Displays a red banner with an actionable 'retry' button.",
            empty="Shows an illustration of an empty folder and a 'create new' button.",
        )


def test_agent_prompt_spec_valid() -> None:
    route = Route(
        path="/upload",
        name="Upload Page",
        purpose="Allows the user to upload their Excel sheet for processing.",
        is_protected=True,
    )
    story = UserStory(
        as_a="Data Analyst",
        i_want_to="upload my Excel sheet and automatically classify the data",
        so_that="I can save 2 hours a day and avoid manual entry errors",
        acceptance_criteria=["Criterion 1"],
        target_route="/upload",
    )
    sm = StateMachine(
        success="Displays a green checkmark and a button to proceed to dashboard.",
        loading="Shows a spinning wheel with 'processing your request...' text.",
        error="Displays a red banner with an actionable 'retry' button.",
        empty="Shows an illustration of an empty folder and a 'create new' button.",
    )
    spec = AgentPromptSpec(
        sitemap=[route],
        routing_and_constraints="Must use Next.js App Router. Authenticated users only.",
        core_user_story=story,
        state_machine=sm,
        validation_rules=["File size must be <5MB", "Only .xlsx and .csv allowed"],
        mermaid_flowchart="graph TD; A-->B; B-->C; C-->D",
    )
    assert spec.sitemap[0].path == "/upload"


def test_agent_prompt_spec_invalid() -> None:
    with pytest.raises(ValidationError):
        AgentPromptSpec(
            sitemap=[],  # invalid length
            routing_and_constraints="Must use Next.js App Router.",
            core_user_story=None,
            state_machine=None,
            validation_rules=[],  # invalid length
            mermaid_flowchart="graph TD;",  # invalid length
        )
