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
        customer_profile=profile, value_map=vmap, fit_evaluation="Good fit between profile and map"
    )

    tool = AlternativeTool(
        name="Excel Spreadsheet Tool",
        financial_cost="$10 per month",
        time_cost="2 hours per day",
        ux_friction="Manual data entry friction",
    )
    analysis = AlternativeAnalysis(
        current_alternatives=[tool],
        switching_cost="High cost of migration",
        ten_x_value="Automated scheduling 10x faster",
    )

    state.value_proposition = canvas
    state.alternative_analysis = analysis

    assert state.value_proposition is not None
    assert state.alternative_analysis is not None

    # Phase 3
    tower = MentalTower(belief="I don't want to waste time.", cognitive_tasks=["Checking calendar"])
    diagram = MentalModelDiagram(towers=[tower], feature_alignment="Feature X aligns")

    phase1 = JourneyPhase(
        phase_name="Awareness of problem",
        touchpoint="Google Search engine",
        customer_action="Searches for solutions",
        mental_tower_ref="Time management",
        pain_points=["Hard to organize meetings manually"],
        emotion_score=-1,
    )
    phase2 = JourneyPhase(
        phase_name="Consideration Phase",
        touchpoint="Company Website Landing Page",
        customer_action="Reads website content",
        mental_tower_ref="Time management",
        pain_points=["Hard to organize meetings manually"],
        emotion_score=0,
    )
    phase3 = JourneyPhase(
        phase_name="Using Product",
        touchpoint="Mobile App Interface",
        customer_action="Creates an account",
        mental_tower_ref="Time management",
        pain_points=["Hard to organize meetings manually"],
        emotion_score=1,
    )
    journey = CustomerJourney(phases=[phase1, phase2, phase3], worst_pain_phase="Using Product")

    route = Route(path="/", name="Home", purpose="Landing page for users", is_protected=False)
    story = UserStory(
        as_a="Regular Platform User",
        i_want_to="Login securely to my dashboard",
        so_that="Use the application features",
        acceptance_criteria=["Login button should be visible and working"],
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
        metric_name="User Retention Rate",
        target_value="> 40% conversion rate",
        measurement_method="Mixpanel Analytics",
    )
    plan = ExperimentPlan(
        riskiest_assumption="Will users pay for this service?",
        experiment_type="Landing Page A/B Test",
        acquisition_channel="Google Ads marketing",
        aarrr_metrics=[metric],
        pivot_condition="No signups after 2 weeks",
    )

    state_machine = StateMachine(
        success="Grid layout", loading="Skeleton screen", error="Error message", empty="Empty state"
    )
    spec = AgentPromptSpec(
        sitemap="Home Landing Page Sitemap",
        routing_and_constraints="Next.js App Router rules",
        core_user_story=story,
        state_machine=state_machine,
        validation_rules="Zod schema validation logic",
        mermaid_flowchart="graph TD; A-->B;",
    )

    state.experiment_plan = plan
    state.agent_prompt_spec = spec

    assert state.experiment_plan is not None
    assert state.agent_prompt_spec is not None
