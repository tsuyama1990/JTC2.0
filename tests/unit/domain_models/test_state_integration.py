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
        customer_profile=profile,
        value_map=vmap,
        fit_evaluation="The AI scheduler perfectly fits the requirements",
    )

    tool = AlternativeTool(
        name="Excel Program",
        financial_cost="10 dollars",
        time_cost="2 hours time",
        ux_friction="Manual work",
    )
    analysis = AlternativeAnalysis(
        current_alternatives=[tool],
        switching_cost="High switching cost",
        ten_x_value="Automated work",
    )

    state.value_proposition = canvas
    state.alternative_analysis = analysis

    assert state.value_proposition is not None
    assert state.alternative_analysis is not None

    # Phase 3
    tower = MentalTower(belief="I don't want to waste time.", cognitive_tasks=["Checking calendar"])
    diagram = MentalModelDiagram(towers=[tower], feature_alignment="Feature X aligns")

    phase1 = JourneyPhase(
        phase_name="Awareness phase",
        touchpoint="Google Search Page",
        customer_action="Searches the web",
        mental_tower_ref="Time requirement",
        pain_points=["Hard to find"],
        emotion_score=-1,
    )
    phase2 = JourneyPhase(
        phase_name="Consideration phase",
        touchpoint="Company Website",
        customer_action="Reads the page",
        mental_tower_ref="Time requirement",
        pain_points=["Hard to find"],
        emotion_score=0,
    )
    phase3 = JourneyPhase(
        phase_name="Using the app",
        touchpoint="Mobile Application",
        customer_action="Creates an account",
        mental_tower_ref="Time requirement",
        pain_points=["Hard to find"],
        emotion_score=1,
    )
    journey = CustomerJourney(phases=[phase1, phase2, phase3], worst_pain_phase="Using the app")

    route = Route(path="/", name="Home Page", purpose="Landing on home", is_protected=False)
    story = UserStory(
        as_a="End User Profile",
        i_want_to="Login to the app",
        so_that="Use app successfully",
        acceptance_criteria=["Login button works"],
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
        metric_name="Retention Metrics",
        target_value="Greater than 40%",
        measurement_method="Mixpanel Analytics",
    )
    plan = ExperimentPlan(
        riskiest_assumption="Will they pay for this?",
        experiment_type="Landing Page Validation",
        acquisition_channel="Facebook Ads",
        aarrr_metrics=[metric],
        pivot_condition="No signups happen",
    )

    state_machine = StateMachine(
        success="Grid view layout",
        loading="Skeleton layout",
        error="Error message",
        empty="Empty state graphic",
    )
    spec = AgentPromptSpec(
        sitemap="Home page route",
        routing_and_constraints="Next.js router rules",
        core_user_story=story,
        state_machine=state_machine,
        validation_rules="Zod validation rules",
        mermaid_flowchart="graph TD Mermaid Chart",
    )

    state.experiment_plan = plan
    state.agent_prompt_spec = spec

    assert state.experiment_plan is not None
    assert state.agent_prompt_spec is not None
