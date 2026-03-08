import pytest
from pydantic import ValidationError

from src.domain_models import (
    AgentPromptSpec,
    AlternativeAnalysis,
    AlternativeTool,
    CustomerJourney,
    CustomerProfile,
    ExperimentPlan,
    JourneyPhase,
    MentalModelDiagram,
    MentalTower,
    MetricTarget,
    Route,
    SitemapAndStory,
    StateMachine,
    UserStory,
    ValueMap,
    ValuePropositionCanvas,
)


def test_customer_profile_valid() -> None:
    profile = CustomerProfile(
        customer_jobs=["Organize meetings"],
        pains=["Meetings take too long"],
        gains=["Save time for deep work"]
    )
    assert profile.customer_jobs == ["Organize meetings"]

def test_customer_profile_invalid_empty() -> None:
    with pytest.raises(ValidationError):
        CustomerProfile(
            customer_jobs=[],
            pains=["Meetings take too long"],
            gains=["Save time for deep work"]
        )

def test_value_proposition_canvas_valid() -> None:
    profile = CustomerProfile(
        customer_jobs=["Organize meetings"],
        pains=["Meetings take too long"],
        gains=["Save time for deep work"]
    )
    vmap = ValueMap(
        products_and_services=["AI Scheduler"],
        pain_relievers=["Automates scheduling"],
        gain_creators=["Blocks out deep work time automatically"]
    )
    canvas = ValuePropositionCanvas(
        customer_profile=profile,
        value_map=vmap,
        fit_evaluation="The AI scheduler perfectly alleviates the pain by automating it."
    )
    assert canvas.fit_evaluation.startswith("The AI")

def test_mental_model_valid() -> None:
    tower = MentalTower(
        belief="I don't want to waste time.",
        cognitive_tasks=["Checking calendar", "Finding overlaps"]
    )
    diagram = MentalModelDiagram(
        towers=[tower],
        feature_alignment="Feature X aligns with the belief of saving time."
    )
    assert len(diagram.towers) == 1

def test_alternative_analysis_valid() -> None:
    tool = AlternativeTool(
        name="Excel",
        financial_cost="$10/month",
        time_cost="2 hours per week",
        ux_friction="Manual data entry is prone to error"
    )
    analysis = AlternativeAnalysis(
        current_alternatives=[tool],
        switching_cost="Need to migrate 10 years of data",
        ten_x_value="Automates 90% of data entry"
    )
    assert len(analysis.current_alternatives) == 1

def test_customer_journey_valid() -> None:
    phase1 = JourneyPhase(
        phase_name="Awareness",
        touchpoint="Google Search",
        customer_action="Searches for solution",
        mental_tower_ref="I don't want to waste time",
        pain_points=["Hard to find good tools"],
        emotion_score=-1
    )
    phase2 = JourneyPhase(
        phase_name="Consideration",
        touchpoint="Website",
        customer_action="Reads features",
        mental_tower_ref="I want it to be easy to use",
        pain_points=["Too much text"],
        emotion_score=0
    )
    phase3 = JourneyPhase(
        phase_name="Using",
        touchpoint="App",
        customer_action="Creates first schedule",
        mental_tower_ref="I want results fast",
        pain_points=["Onboarding is too long"],
        emotion_score=-3
    )

    journey = CustomerJourney(
        phases=[phase1, phase2, phase3],
        worst_pain_phase="Using"
    )
    assert journey.worst_pain_phase == "Using"

def test_customer_journey_invalid_worst_pain_phase() -> None:
    phase1 = JourneyPhase(
        phase_name="Awareness",
        touchpoint="Google Search",
        customer_action="Searches for solution",
        mental_tower_ref="I don't want to waste time",
        pain_points=["Hard to find good tools"],
        emotion_score=-1
    )
    phase2 = JourneyPhase(
        phase_name="Consideration",
        touchpoint="Website",
        customer_action="Reads features",
        mental_tower_ref="I want it to be easy to use",
        pain_points=["Too much text"],
        emotion_score=0
    )
    phase3 = JourneyPhase(
        phase_name="Using",
        touchpoint="App",
        customer_action="Creates first schedule",
        mental_tower_ref="I want results fast",
        pain_points=["Onboarding is too long"],
        emotion_score=-3
    )

    with pytest.raises(ValidationError, match="does not match any existing phase name"):
        CustomerJourney(
            phases=[phase1, phase2, phase3],
            worst_pain_phase="Churn"  # Invalid phase name
        )

def test_customer_journey_invalid_short() -> None:
    phase1 = JourneyPhase(
        phase_name="Awareness",
        touchpoint="Google",
        customer_action="Search",
        mental_tower_ref="Time",
        pain_points=["Hard"],
        emotion_score=0
    )
    with pytest.raises(ValidationError):
        CustomerJourney(
            phases=[phase1, phase1], # Min 3 required
            worst_pain_phase="Awareness"
        )

def test_sitemap_and_story_valid() -> None:
    route = Route(
        path="/dashboard",
        name="Dashboard",
        purpose="Shows main info",
        is_protected=True
    )
    story = UserStory(
        as_a="Manager",
        i_want_to="See all schedules",
        so_that="I can assign tasks",
        acceptance_criteria=["Must load under 2s"],
        target_route="/dashboard"
    )
    sitemap = SitemapAndStory(
        sitemap=[route],
        core_story=story
    )
    assert sitemap.core_story.target_route == "/dashboard"

def test_experiment_plan_valid() -> None:
    metric = MetricTarget(
        metric_name="Day 7 Retention",
        target_value="> 40%",
        measurement_method="Mixpanel"
    )
    plan = ExperimentPlan(
        riskiest_assumption="Users will pay for this",
        experiment_type="Landing Page",
        acquisition_channel="Facebook Ads",
        aarrr_metrics=[metric],
        pivot_condition="< 5% conversion rate"
    )
    assert len(plan.aarrr_metrics) == 1

def test_agent_prompt_spec_valid() -> None:
    story = UserStory(
        as_a="Manager",
        i_want_to="See all schedules",
        so_that="I can assign tasks",
        acceptance_criteria=["Must load under 2s"],
        target_route="/dashboard"
    )
    state = StateMachine(
        success="Grid layout",
        loading="Skeleton",
        error="Error banner",
        empty="Empty state graphic"
    )
    spec = AgentPromptSpec(
        sitemap="Home -> Dashboard",
        routing_and_constraints="Next.js App Router",
        core_user_story=story,
        state_machine=state,
        validation_rules="Zod schema X",
        mermaid_flowchart="graph TD; A-->B;"
    )
    assert spec.mermaid_flowchart == "graph TD; A-->B;"
