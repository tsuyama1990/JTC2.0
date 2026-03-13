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


def test_value_proposition_canvas_valid() -> None:
    cp = CustomerProfile(
        customer_jobs=["Organize data"],
        pains=["Too manual"],
        gains=["Save time"],
    )
    vm = ValueMap(
        products_and_services=["Auto-organizer app"],
        pain_relievers=["Automates manual entry"],
        gain_creators=["Saves 10 hours a week"],
    )
    vpc = ValuePropositionCanvas(
        customer_profile=cp,
        value_map=vm,
        fit_evaluation="Fits perfectly",
    )
    assert vpc.fit_evaluation == "Fits perfectly"


def test_value_proposition_canvas_invalid() -> None:
    with pytest.raises(ValidationError):
        ValuePropositionCanvas.model_validate(
            {
                "customer_profile": {
                    "customer_jobs": ["Job"],
                    "pains": ["Pain"],
                    "gains": ["Gain"],
                },
                "value_map": {
                    "products_and_services": ["Product"],
                    "pain_relievers": ["Reliever"],
                    "gain_creators": ["Creator"],
                },
                "fit_evaluation": "f",  # length 1, min is 3
            }
        )

    # test forbid extra
    with pytest.raises(ValidationError):
        ValuePropositionCanvas.model_validate(
            {
                "customer_profile": {
                    "customer_jobs": ["Job"],
                    "pains": ["Pain"],
                    "gains": ["Gain"],
                },
                "value_map": {
                    "products_and_services": ["Product"],
                    "pain_relievers": ["Reliever"],
                    "gain_creators": ["Creator"],
                },
                "fit_evaluation": "Valid evaluation",
                "extra": "bad",
            }
        )


def test_mental_model_diagram_valid() -> None:
    tower = MentalTower(belief="Time is money", cognitive_tasks=["Prioritizing"])
    mmd = MentalModelDiagram(
        towers=[tower],
        feature_alignment="Aligned properly",
    )
    assert len(mmd.towers) == 1


def test_alternative_analysis_valid() -> None:
    tool = AlternativeTool(name="Excel", financial_cost=10.0, time_cost=100.0, ux_friction="Manual")
    aa = AlternativeAnalysis(
        current_alternatives=[tool],
        switching_cost="Data migration",
        ten_x_value="Automated workflows",
    )
    assert len(aa.current_alternatives) == 1


def test_customer_journey_valid() -> None:
    phase1 = JourneyPhase(
        phase_name="認知",
        touchpoint="Ad",
        customer_action="Clicks",
        mental_tower_ref="Needs better tool",
        pain_points=["Confused"],
        emotion_score=-1,
    )
    phase2 = JourneyPhase(
        phase_name="検討",
        touchpoint="Website",
        customer_action="Fills form",
        mental_tower_ref="Hopeful",
        pain_points=["Long form"],
        emotion_score=0,
    )
    phase3 = JourneyPhase(
        phase_name="利用中",
        touchpoint="App",
        customer_action="Uses feature",
        mental_tower_ref="Wants results",
        pain_points=["None"],
        emotion_score=5,
    )
    cj = CustomerJourney(phases=[phase1, phase2, phase3], worst_pain_phase="認知")
    assert len(cj.phases) == 3


def test_customer_journey_invalid() -> None:
    phase = JourneyPhase(
        phase_name="認知",
        touchpoint="Ad",
        customer_action="Clicks",
        mental_tower_ref="Needs better tool",
        pain_points=["Confused"],
        emotion_score=-1,
    )
    with pytest.raises(ValidationError):
        # min length is 3
        CustomerJourney(phases=[phase], worst_pain_phase="認知")


def test_sitemap_and_story_valid() -> None:
    route = Route(path="/", name="Home", purpose="Landing", is_protected=False)
    story = UserStory(
        as_a="User",
        i_want_to="Login",
        so_that="I can use the app",
        acceptance_criteria=["Can login"],
        target_route="/login",
    )
    sas = SitemapAndStory(sitemap=[route], core_story=story)
    assert len(sas.sitemap) == 1


def test_experiment_plan_valid() -> None:
    metric = MetricTarget(
        metric_name="Retention", target_value="40%", measurement_method="Mixpanel"
    )
    ep = ExperimentPlan(
        riskiest_assumption="Users will pay",
        experiment_type="Landing Page",
        acquisition_channel="Ads",
        aarrr_metrics=[metric],
        pivot_condition="No signups",
    )
    assert ep.experiment_type == "Landing Page"


def test_agent_prompt_spec_valid() -> None:
    story = UserStory(
        as_a="User",
        i_want_to="Login",
        so_that="I can use the app",
        acceptance_criteria=["Can login"],
        target_route="/login",
    )
    sm = StateMachine(
        success="Success layout",
        loading="Skeleton UI",
        error="Error UI",
        empty="Empty state",
    )
    aps = AgentPromptSpec(
        sitemap="Sitemap desc",
        routing_and_constraints="Next.js",
        core_user_story=story,
        state_machine=sm,
        validation_rules="Zod schema",
        mermaid_flowchart="graph TD;",
    )
    assert aps.routing_and_constraints == "Next.js"
