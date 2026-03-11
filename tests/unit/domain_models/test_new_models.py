import pytest
from pydantic import ValidationError

from src.domain_models.agent_spec import AgentPromptSpec, StateMachine
from src.domain_models.alternative_analysis import AlternativeAnalysis, AlternativeTool
from src.domain_models.customer_journey import CustomerJourney, JourneyPhase
from src.domain_models.experiment_plan import ExperimentPlan, MetricTarget
from src.domain_models.mental_model import MentalModelDiagram, MentalTower
from src.domain_models.sitemap import Route, SitemapAndStory, UserStory
from src.domain_models.value_proposition import CustomerProfile, ValueMap, ValuePropositionCanvas


def test_value_proposition_canvas_valid() -> None:
    profile = CustomerProfile(
        customer_jobs=["A"],
        pains=["B"],
        gains=["C"],
    )
    vmap = ValueMap(
        products_and_services=["D"],
        pain_relievers=["E"],
        gain_creators=["F"],
    )
    vpc = ValuePropositionCanvas(
        customer_profile=profile,
        value_map=vmap,
        fit_evaluation="Good fit",
    )
    assert vpc.fit_evaluation == "Good fit"


def test_value_proposition_canvas_extra_forbid() -> None:
    with pytest.raises(ValidationError):
        CustomerProfile.model_validate(
            {
                "customer_jobs": ["A"],
                "pains": ["B"],
                "gains": ["C"],
                "extra": "bad",
            }
        )


def test_mental_model_valid() -> None:
    tower = MentalTower(belief="Belief", cognitive_tasks=["Task1"])
    diagram = MentalModelDiagram(towers=[tower], feature_alignment="Aligned")
    assert diagram.feature_alignment == "Aligned"
    assert len(diagram.towers) == 1


def test_alternative_analysis_valid() -> None:
    tool = AlternativeTool(
        name="Excel", financial_cost="Free", time_cost="High", ux_friction="Manual entry"
    )
    analysis = AlternativeAnalysis(
        current_alternatives=[tool], switching_cost="Low", ten_x_value="Automation"
    )
    assert analysis.ten_x_value == "Automation"


def test_customer_journey_valid() -> None:
    phases = [
        JourneyPhase(
            phase_name=f"Phase {i}",
            touchpoint="App",
            customer_action="Click",
            mental_tower_ref="Belief",
            pain_points=["Slow"],
            emotion_score=3,
        )
        for i in range(3)
    ]
    journey = CustomerJourney(phases=phases, worst_pain_phase="Phase 0")
    assert len(journey.phases) == 3


def test_customer_journey_invalid_emotion_score() -> None:
    with pytest.raises(ValidationError):
        JourneyPhase(
            phase_name="Phase 1",
            touchpoint="App",
            customer_action="Click",
            mental_tower_ref="Belief",
            pain_points=["Slow"],
            emotion_score=10,  # Invalid, > 5
        )


def test_customer_journey_invalid_length() -> None:
    phases = [
        JourneyPhase(
            phase_name=f"Phase {i}",
            touchpoint="App",
            customer_action="Click",
            mental_tower_ref="Belief",
            pain_points=["Slow"],
            emotion_score=3,
        )
        for i in range(2)  # Invalid, < 3
    ]
    with pytest.raises(ValidationError):
        CustomerJourney(phases=phases, worst_pain_phase="Phase 0")


def test_sitemap_and_story_valid() -> None:
    route = Route(path="/login", name="Login", purpose="Auth", is_protected=False)
    story = UserStory(
        as_a="User",
        i_want_to="Login",
        so_that="I can use app",
        acceptance_criteria=["Works"],
        target_route="/login",
    )
    sitemap = SitemapAndStory(sitemap=[route], core_story=story)
    assert sitemap.core_story.as_a == "User"


def test_experiment_plan_valid() -> None:
    metric = MetricTarget(
        metric_name="Retention", target_value="40%", measurement_method="Mixpanel"
    )
    plan = ExperimentPlan(
        riskiest_assumption="Will they pay",
        experiment_type="LP",
        acquisition_channel="Ads",
        aarrr_metrics=[metric],
        pivot_condition="< 5% CTR",
    )
    assert plan.experiment_type == "LP"


def test_agent_prompt_spec_valid() -> None:
    state_machine = StateMachine(
        success="Layout", loading="Skeleton", error="Error UI", empty="No data UI"
    )
    story = UserStory(
        as_a="User",
        i_want_to="Login",
        so_that="I can use app",
        acceptance_criteria=["Works"],
        target_route="/login",
    )
    spec = AgentPromptSpec(
        sitemap="Sitemap text",
        routing_and_constraints="Next.js",
        core_user_story=story,
        state_machine=state_machine,
        validation_rules="Zod",
        mermaid_flowchart="graph TD",
    )
    assert spec.sitemap == "Sitemap text"
