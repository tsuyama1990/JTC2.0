import pytest
from pydantic import ValidationError

from src.domain_models.agent_prompt_spec import AgentPromptSpec, StateMachine
from src.domain_models.alternative_analysis import AlternativeAnalysis, AlternativeTool
from src.domain_models.customer_journey import CustomerJourney, JourneyPhase
from src.domain_models.experiment_plan import ExperimentPlan, MetricTarget
from src.domain_models.mental_model_diagram import MentalModelDiagram, MentalTower
from src.domain_models.sitemap_and_story import Route, SitemapAndStory, UserStory
from src.domain_models.value_proposition_canvas import (
    CustomerProfile,
    ValueMap,
    ValuePropositionCanvas,
)


def test_alternative_analysis_valid() -> None:
    tool = AlternativeTool(
        name="Excel", financial_cost="Low", time_cost="High", ux_friction="Manual entry"
    )
    analysis = AlternativeAnalysis(
        current_alternatives=[tool], switching_cost="High", ten_x_value="Automation"
    )
    assert analysis.switching_cost == "High"
    assert len(analysis.current_alternatives) == 1


def test_alternative_analysis_extra_forbid() -> None:
    with pytest.raises(ValidationError):
        AlternativeAnalysis.model_validate(
            {"current_alternatives": [], "switching_cost": "", "ten_x_value": "", "extra": "bad"}
        )


def test_vpc_valid() -> None:
    profile = CustomerProfile(
        customer_jobs=["Organize data"], pains=["Too manual"], gains=["Save time"]
    )
    val_map = ValueMap(
        products_and_services=["SaaS"], pain_relievers=["Automation"], gain_creators=["Dashboards"]
    )
    vpc = ValuePropositionCanvas(
        customer_profile=profile, value_map=val_map, fit_evaluation="Good fit"
    )
    assert vpc.fit_evaluation == "Good fit"


def test_mental_model_diagram_valid() -> None:
    tower = MentalTower(belief="Time is money", cognitive_tasks=["Calculate ROI"])
    diagram = MentalModelDiagram(towers=[tower], feature_alignment="Automation aligns with time")
    assert len(diagram.towers) == 1


def test_customer_journey_valid() -> None:
    phase = JourneyPhase(
        phase_name="Awareness",
        touchpoint="Ad",
        customer_action="Clicks",
        mental_tower_ref="Curiosity",
        pain_points=["Confusing ad"],
        emotion_score=0,
    )
    phase2 = JourneyPhase(
        phase_name="Consideration",
        touchpoint="Website",
        customer_action="Reads",
        mental_tower_ref="Research",
        pain_points=["Too much text"],
        emotion_score=-1,
    )
    phase3 = JourneyPhase(
        phase_name="Purchase",
        touchpoint="Checkout",
        customer_action="Buys",
        mental_tower_ref="Commitment",
        pain_points=["Slow load"],
        emotion_score=2,
    )
    journey = CustomerJourney(phases=[phase, phase2, phase3], worst_pain_phase="Awareness")
    assert len(journey.phases) == 3


def test_customer_journey_min_length() -> None:
    phase = JourneyPhase(
        phase_name="Awareness",
        touchpoint="Ad",
        customer_action="Clicks",
        mental_tower_ref="Curiosity",
        pain_points=["Confusing ad"],
        emotion_score=0,
    )
    with pytest.raises(ValidationError):
        CustomerJourney(phases=[phase], worst_pain_phase="Awareness")


def test_sitemap_and_story_valid() -> None:
    route = Route(path="/", name="Home", purpose="Landing", is_protected=False)
    story = UserStory(
        as_a="User",
        i_want_to="Login",
        so_that="Access data",
        acceptance_criteria=["Can login"],
        target_route="/login",
    )
    sitemap = SitemapAndStory(sitemap=[route], core_story=story)
    assert sitemap.core_story.as_a == "User"


def test_experiment_plan_valid() -> None:
    metric = MetricTarget(
        metric_name="Retention", target_value="40%", measurement_method="Mixpanel"
    )
    plan = ExperimentPlan(
        riskiest_assumption="Users will pay",
        experiment_type="LP",
        acquisition_channel="Ads",
        aarrr_metrics=[metric],
        pivot_condition="<10% conversion",
    )
    assert plan.experiment_type == "LP"


def test_agent_prompt_spec_valid() -> None:
    sm = StateMachine(success="UI", loading="Spinner", error="Retry", empty="No data")
    story = UserStory(
        as_a="User",
        i_want_to="Login",
        so_that="Access data",
        acceptance_criteria=["Can login"],
        target_route="/login",
    )
    spec = AgentPromptSpec(
        sitemap="Paths",
        routing_and_constraints="Next.js",
        core_user_story=story,
        state_machine=sm,
        validation_rules="Zod",
        mermaid_flowchart="graph TD",
    )
    assert spec.routing_and_constraints == "Next.js"
