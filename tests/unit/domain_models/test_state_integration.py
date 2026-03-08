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
from src.domain_models.state import GlobalState


def test_global_state_updates_with_remastered_models() -> None:
    state = GlobalState(topic="Test")

    # Phase 2
    profile = CustomerProfile(
        customer_jobs=["Organize meetings"],
        pains=["Meetings take too long"],
        gains=["Save time for deep work"],
    )
    vmap = ValueMap(
        products_and_services=["AI Scheduler"],
        pain_relievers=["Automates scheduling"],
        gain_creators=["Blocks out deep work time automatically"],
    )
    canvas = ValuePropositionCanvas(
        customer_profile=profile, value_map=vmap, fit_evaluation="Good fit"
    )

    tool = AlternativeTool(
        name="Excel", financial_cost="$10", time_cost="2 hours", ux_friction="Manual"
    )
    analysis = AlternativeAnalysis(
        current_alternatives=[tool], switching_cost="High", ten_x_value="Automated"
    )

    state.value_proposition = canvas
    state.alternative_analysis = analysis

    assert state.value_proposition is not None
    assert state.alternative_analysis is not None

    # Phase 3
    tower = MentalTower(belief="I don't want to waste time.", cognitive_tasks=["Checking calendar"])
    diagram = MentalModelDiagram(towers=[tower], feature_alignment="Feature X aligns")

    phase1 = JourneyPhase(
        phase_name="Awareness",
        touchpoint="Google Search",
        customer_action="Searches",
        mental_tower_ref="Time",
        pain_points=["Hard"],
        emotion_score=-1,
    )
    phase2 = JourneyPhase(
        phase_name="Consideration",
        touchpoint="Website",
        customer_action="Reads",
        mental_tower_ref="Time",
        pain_points=["Hard"],
        emotion_score=0,
    )
    phase3 = JourneyPhase(
        phase_name="Using",
        touchpoint="App",
        customer_action="Creates",
        mental_tower_ref="Time",
        pain_points=["Hard"],
        emotion_score=1,
    )
    journey = CustomerJourney(phases=[phase1, phase2, phase3], worst_pain_phase="Using")

    route = Route(path="/", name="Home", purpose="Landing", is_protected=False)
    story = UserStory(
        as_a="User",
        i_want_to="Login",
        so_that="Use app",
        acceptance_criteria=["Login button"],
        target_route="/",
    )
    sitemap = SitemapAndStory(sitemap=[route], core_story=story)

    state.mental_model = diagram
    state.customer_journey = journey
    state.sitemap_and_story = sitemap

    assert state.mental_model is not None
    assert state.customer_journey is not None
    assert state.sitemap_and_story is not None

    # Phase 5 & 6
    metric = MetricTarget(
        metric_name="Retention", target_value="> 40%", measurement_method="Mixpanel"
    )
    plan = ExperimentPlan(
        riskiest_assumption="Will they pay?",
        experiment_type="Landing Page",
        acquisition_channel="Ads",
        aarrr_metrics=[metric],
        pivot_condition="No signups",
    )

    state_machine = StateMachine(success="Grid", loading="Skeleton", error="Error", empty="Empty")
    spec = AgentPromptSpec(
        sitemap="Home",
        routing_and_constraints="Next.js",
        core_user_story=story,
        state_machine=state_machine,
        validation_rules="Zod",
        mermaid_flowchart="graph TD",
    )

    state.experiment_plan = plan
    state.agent_prompt_spec = spec

    assert state.experiment_plan is not None
    assert state.agent_prompt_spec is not None
