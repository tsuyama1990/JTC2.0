from collections.abc import Iterator

import pytest
from pydantic import ValidationError

from src.core.config import get_settings
from src.domain_models.metrics import AARRR, DetailedMetrics, Metrics
from src.domain_models.mvp import MVP, Feature, MVPType, Priority
from src.domain_models.persona import EmpathyMap, Persona
from src.domain_models.simulation import AgentState, DeGrootProfile, Role
from src.domain_models.state import GlobalState, Phase


def test_persona_creation() -> None:
    empathy = EmpathyMap(
        says=["I want this"],
        thinks=["Is it worth it?"],
        does=["Search online"],
        feels=["Confused"],
    )
    persona = Persona(
        name="John Doe",
        occupation="Developer",
        demographics="30, Male, New York",
        goals=["Learn Python"],
        frustrations=["No time"],
        bio="A busy developer looking to improve skills.",
        empathy_map=empathy,
        is_fact_based=True,
        interview_insights=["Insight 1"],
    )
    assert persona.name == "John Doe"
    assert persona.empathy_map is not None
    assert persona.empathy_map.says == ["I want this"]
    assert persona.is_fact_based is True
    assert len(persona.interview_insights) == 1


def test_persona_validation_error() -> None:
    """Test validation limits for Persona."""
    with pytest.raises(ValidationError) as exc:
        Persona(
            name="J",  # Too short
            occupation="D",
            demographics="M",
            goals=[],  # Empty
            frustrations=[],
            bio="Sh",  # Too short
        )
    errors = exc.value.errors()
    assert any(e["loc"] == ("name",) for e in errors)
    assert any(e["loc"] == ("occupation",) for e in errors)
    assert any(e["loc"] == ("goals",) for e in errors)
    assert any(e["loc"] == ("bio",) for e in errors)


def test_mvp_creation() -> None:
    feature = Feature(
        name="Login System",
        description="Allow users to login via OAuth.",
        priority=Priority.MUST_HAVE,
    )
    mvp = MVP(
        type=MVPType.LANDING_PAGE,
        core_features=[feature],
        success_criteria="Achieve 100 signups within the first week.",
        v0_url="https://v0.dev/test",
        deployment_status="deployed",
    )
    assert mvp.type == MVPType.LANDING_PAGE
    assert mvp.core_features[0].priority == Priority.MUST_HAVE
    # Check string representation or HttpUrl properties
    assert str(mvp.v0_url) == "https://v0.dev/test"
    assert mvp.deployment_status == "deployed"


def test_mvp_feature_validation() -> None:
    """Test feature validation."""
    # settings.validation.min_content_length is 3. "Short" is 5.
    # We need a string shorter than 3 characters to trigger the error.
    with pytest.raises(ValidationError):
        Feature(
            name="Login",
            description="No",  # Length 2 < 3
            priority=Priority.MUST_HAVE,
        )


def test_mvp_invalid_priority() -> None:
    """Test that invalid priority strings are rejected."""
    with pytest.raises(ValidationError):
        Feature(
            name="Login",
            description="Login feature description.",
            priority="super-important",
        )


def test_metrics_creation() -> None:
    detailed = DetailedMetrics(
        planning_score=0.8,
        communication_score=0.9,
    )
    metrics = Metrics(
        aarrr=AARRR(acquisition=100.0, activation=50.0),
        detailed=detailed,
        custom_metrics={"nps": 9.0},
    )
    assert metrics.aarrr.acquisition == 100.0
    assert metrics.detailed.planning_score == 0.8
    assert metrics.custom_metrics["nps"] == 9.0


def test_metrics_numeric_validation() -> None:
    """Test numeric range validation."""
    with pytest.raises(ValidationError) as exc:
        AARRR(acquisition=-10.0, retention=150.0)

    errors = exc.value.errors()
    assert any(e["loc"] == ("acquisition",) for e in errors)
    assert any(e["loc"] == ("retention",) for e in errors)


def test_metrics_limit_custom() -> None:
    """Test that custom metrics are limited."""
    settings = get_settings()
    # Create a dict with VAL_MAX_CUSTOM_METRICS + 1 entries
    excessive_metrics = {
        f"metric_{i}": float(i) for i in range(settings.validation.max_custom_metrics + 1)
    }

    with pytest.raises(ValidationError) as exc:
        Metrics(custom_metrics=excessive_metrics)

    assert "Too many custom metrics" in str(exc.value)


def test_global_state_lifecycle_validation() -> None:
    """Test GlobalState phase transition validation."""
    state = GlobalState()
    assert state.phase == Phase.IDEATION

    settings = get_settings()

    # Should allow VERIFICATION transition only with persona
    state.phase = Phase.VERIFICATION
    with pytest.raises(ValidationError) as exc:
        GlobalState.model_validate(state.model_dump())
    assert settings.errors.missing_persona in str(exc.value)

    # Correct transition
    state.target_persona = Persona(
        name="Alice",
        occupation="Manager",
        demographics="40, Female, London",
        goals=["Efficiency"],
        frustrations=["Slow tools"],
        bio="Experienced manager.",
    )
    state.phase = Phase.VERIFICATION
    # Should pass now
    GlobalState.model_validate(state.model_dump())

    # Should allow SOLUTION transition only with MVP
    state.phase = Phase.SOLUTION
    with pytest.raises(ValidationError) as exc:
        GlobalState.model_validate(state.model_dump())
    assert settings.errors.missing_mvp in str(exc.value)


def test_agent_state_creation() -> None:
    """Test AgentState and DeGrootProfile."""
    profile = DeGrootProfile(self_confidence=0.8, influence_weights={"Sales Manager": 0.2})
    agent_state = AgentState(role=Role.FINANCE, degroot_profile=profile)
    assert agent_state.degroot_profile.self_confidence == 0.8
    assert agent_state.degroot_profile.influence_weights["Sales Manager"] == 0.2

    # Validation
    with pytest.raises(ValidationError):
        DeGrootProfile(self_confidence=1.5)  # Should be <= 1.0


def test_agent_states_validation() -> None:
    """Test agent_states key validation."""
    profile = DeGrootProfile(self_confidence=0.5)

    # Valid
    valid_states = {Role.FINANCE: AgentState(role=Role.FINANCE, degroot_profile=profile)}
    GlobalState(agent_states=valid_states)

    # Invalid key mismatch
    invalid_states = {Role.SALES: AgentState(role=Role.FINANCE, degroot_profile=profile)}
    with pytest.raises(ValidationError, match="Key Sales Manager does not match"):
        GlobalState(agent_states=invalid_states)


def test_value_proposition_canvas() -> None:
    from src.domain_models.persona import CustomerProfile, ValueMap, ValuePropositionCanvas

    profile = CustomerProfile(
        customer_jobs=["Do work"], pains=["Too much work"], gains=["More free time"]
    )
    vmap = ValueMap(
        products_and_services=["App"],
        pain_relievers=["Automates work"],
        gain_creators=["Saves time"],
    )
    canvas = ValuePropositionCanvas(
        customer_profile=profile, value_map=vmap, fit_evaluation="Perfect fit"
    )
    assert canvas.fit_evaluation == "Perfect fit"
    with pytest.raises(ValidationError):
        ValuePropositionCanvas.model_validate(
            {
                "customer_profile": profile.model_dump(),
                "value_map": vmap.model_dump(),
                "fit_evaluation": "Perfect fit",
                "extra_field": "bad",
            }
        )


def test_mental_model_diagram() -> None:
    from src.domain_models.persona import MentalModelDiagram, MentalTower

    tower = MentalTower(belief="Time is money", cognitive_tasks=["Calculate ROI"])
    diagram = MentalModelDiagram(towers=[tower], feature_alignment="Aligned")
    assert len(diagram.towers) == 1
    with pytest.raises(ValidationError):
        MentalModelDiagram.model_validate(
            {"towers": [tower.model_dump()], "feature_alignment": "Aligned", "extra": "bad"}
        )


def test_alternative_analysis() -> None:
    from src.domain_models.mvp import AlternativeAnalysis, AlternativeTool

    tool = AlternativeTool(name="Excel", financial_cost="$10", time_cost="High", ux_friction="High")
    analysis = AlternativeAnalysis(
        current_alternatives=[tool], switching_cost="Low", ten_x_value="10x faster"
    )
    assert analysis.ten_x_value == "10x faster"
    with pytest.raises(ValidationError):
        AlternativeAnalysis.model_validate(
            {
                "current_alternatives": [tool.model_dump()],
                "switching_cost": "Low",
                "ten_x_value": "10x faster",
                "extra": "bad",
            }
        )


def test_customer_journey() -> None:
    from src.domain_models.mvp import CustomerJourney, JourneyPhase

    phase = JourneyPhase(
        phase_name="Discovery",
        touchpoint="Ad",
        customer_action="Click",
        mental_tower_ref="Curiosity",
        pain_points=["Confusing ad"],
        emotion_score=0,
    )
    journey = CustomerJourney(phases=[phase, phase, phase], worst_pain_phase="Discovery")
    assert len(journey.phases) == 3

    with pytest.raises(ValidationError):
        # min_length is 3
        CustomerJourney(phases=[phase, phase], worst_pain_phase="Discovery")

    with pytest.raises(ValidationError):
        CustomerJourney.model_validate(
            {
                "phases": [phase.model_dump(), phase.model_dump(), phase.model_dump()],
                "worst_pain_phase": "Discovery",
                "extra": "bad",
            }
        )


def test_sitemap_and_story() -> None:
    from src.domain_models.mvp import Route, SitemapAndStory, UserStory

    route = Route(path="/", name="Home", purpose="Landing", is_protected=False)
    story = UserStory(
        as_a="User",
        i_want_to="Login",
        so_that="I can work",
        acceptance_criteria=["Works"],
        target_route="/",
    )
    sitemap = SitemapAndStory(sitemap=[route], core_story=story)
    assert sitemap.sitemap[0].name == "Home"
    with pytest.raises(ValidationError):
        SitemapAndStory.model_validate(
            {
                "sitemap": [route.model_dump()],
                "core_story": story.model_dump(),
                "extra": "bad",
            }
        )


def test_experiment_plan() -> None:
    from src.domain_models.metrics import ExperimentPlan, MetricTarget

    target = MetricTarget(
        metric_name="Retention", target_value="10%", measurement_method="Mixpanel"
    )
    plan = ExperimentPlan(
        riskiest_assumption="Users will pay",
        experiment_type="LP",
        acquisition_channel="Ads",
        aarrr_metrics=[target],
        pivot_condition="No signups",
    )
    assert len(plan.aarrr_metrics) == 1
    with pytest.raises(ValidationError):
        ExperimentPlan.model_validate(
            {
                "riskiest_assumption": "Users will pay",
                "experiment_type": "LP",
                "acquisition_channel": "Ads",
                "aarrr_metrics": [target.model_dump()],
                "pivot_condition": "No signups",
                "extra": "bad",
            }
        )


def test_agent_prompt_spec() -> None:
    from src.domain_models.mvp import AgentPromptSpec, StateMachine, UserStory

    machine = StateMachine(success="Done", loading="Wait", error="Fail", empty="Empty")
    story = UserStory(
        as_a="User",
        i_want_to="Login",
        so_that="I can work",
        acceptance_criteria=["Works"],
        target_route="/",
    )
    spec = AgentPromptSpec(
        sitemap="sitemap string",
        routing_and_constraints="constraints",
        core_user_story=story,
        state_machine=machine,
        validation_rules="rules",
        mermaid_flowchart="graph TD",
    )
    assert spec.mermaid_flowchart == "graph TD"
    with pytest.raises(ValidationError):
        AgentPromptSpec.model_validate(
            {
                "sitemap": "sitemap string",
                "routing_and_constraints": "constraints",
                "core_user_story": story.model_dump(),
                "state_machine": machine.model_dump(),
                "validation_rules": "rules",
                "mermaid_flowchart": "graph TD",
                "extra": "bad",
            }
        )


def test_lazy_idea_iterator_edges() -> None:
    from src.core.config import get_settings
    from src.domain_models.common import LazyIdeaIterator
    from src.domain_models.lean_canvas import LeanCanvas

    settings = get_settings()

    def gen() -> Iterator[LeanCanvas]:
        for i in range(settings.iterator_safety_limit + 5):
            yield LeanCanvas(
                id=i,
                title="Test Idea",
                problem="Too slow processes",
                customer_segments="Devs",
                unique_value_prop="Fast tools are great",
                solution="Build fast things",
            )

    iterator = LazyIdeaIterator(gen())

    # Test __iter__
    assert iter(iterator) is iterator

    # Consume exactly iterator_safety_limit items
    for _ in range(settings.iterator_safety_limit):
        item = next(iterator)
        assert item.title == "Test Idea"

    # The next call should raise StopIteration
    with pytest.raises(StopIteration):
        next(iterator)


def test_lean_canvas_validation_edges() -> None:
    from src.domain_models.lean_canvas import LeanCanvas

    # Title too short
    with pytest.raises(ValidationError) as exc:
        LeanCanvas(
            id=1,
            title="ab",
            problem="a b c",
            customer_segments="devs",
            unique_value_prop="a b c",
            solution="a b c",
        )
    assert "Title must be at least 3 characters long" in str(exc.value)

    # Content < 3 words
    with pytest.raises(ValidationError) as exc:
        LeanCanvas(
            id=1,
            title="abc",
            problem="a b",
            customer_segments="devs",
            unique_value_prop="a b c",
            solution="a b c",
        )
    assert "Content must contain at least 3 words" in str(exc.value)


def test_metrics_custom_key_validation() -> None:
    from src.domain_models.metrics import Metrics

    # Invalid key
    with pytest.raises(ValidationError) as exc:
        Metrics(custom_metrics={"bad-key!": 5.0})
    assert "Invalid metric key" in str(exc.value)

    # Value too small
    with pytest.raises(ValidationError) as exc:
        Metrics(custom_metrics={"valid_key": -100.0})
    assert "must be >=" in str(exc.value)

    # Value too large
    with pytest.raises(ValidationError) as exc:
        Metrics(custom_metrics={"valid_key": 2000000.0})
    assert "exceeds maximum allowed threshold" in str(exc.value)


def test_mvpspec_v0_url_and_components_edges() -> None:
    from src.domain_models.mvp import MVP, MVPType, Priority

    # Invalid URL domain
    with pytest.raises(ValidationError) as exc:
        MVP.model_validate(
            {
                "type": MVPType.LANDING_PAGE,
                "core_features": [
                    {"name": "A" * 10, "description": "A" * 10, "priority": Priority.MUST_HAVE}
                ],
                "success_criteria": "A" * 10,
                "v0_url": "https://evil.com",
            }
        )
    assert "Only v0.dev is allowed" in str(exc.value)

    # Invalid URL scheme
    with pytest.raises(ValidationError) as exc:
        MVP.model_validate(
            {
                "type": MVPType.LANDING_PAGE,
                "core_features": [
                    {"name": "A" * 10, "description": "A" * 10, "priority": Priority.MUST_HAVE}
                ],
                "success_criteria": "A" * 10,
                "v0_url": "ftp://v0.dev",
            }
        )
    assert "URL scheme" in str(exc.value)

    # Path traversal
    with pytest.raises(ValidationError) as exc:
        MVP.model_validate(
            {
                "type": MVPType.LANDING_PAGE,
                "core_features": [
                    {"name": "A" * 10, "description": "A" * 10, "priority": Priority.MUST_HAVE}
                ],
                "success_criteria": "A" * 10,
                "v0_url": "https://v0.dev/..//path",
            }
        )
    assert "Path traversal detected" in str(exc.value)

    from src.domain_models.mvp import MVPSpec

    # Component name non-ascii
    with pytest.raises(ValidationError) as exc:
        MVPSpec(app_name="App", core_feature="A" * 10, components=["コンポーネント"])
    assert "must be ASCII" in str(exc.value)

    # Component name too long
    with pytest.raises(ValidationError) as exc:
        MVPSpec(app_name="App", core_feature="A" * 10, components=["A" * 51])
    assert "too long" in str(exc.value)

    # HTML tag in v0_prompt
    with pytest.raises(ValidationError) as exc:
        MVPSpec(app_name="App", core_feature="A" * 10, v0_prompt="<b>bold</b>")
    assert "must not contain HTML" in str(exc.value)


def test_persona_interview_insights_edges() -> None:
    from src.domain_models.persona import Persona

    # Insight too short
    with pytest.raises(ValidationError) as exc:
        Persona(
            name="A" * 10,
            occupation="A" * 10,
            demographics="A" * 10,
            goals=["A" * 10],
            frustrations=["A" * 10],
            bio="A" * 10,
            interview_insights=["shrt"],
        )
    assert "is too short" in str(exc.value)

    # Insight too long
    with pytest.raises(ValidationError) as exc:
        Persona(
            name="A" * 10,
            occupation="A" * 10,
            demographics="A" * 10,
            goals=["A" * 10],
            frustrations=["A" * 10],
            bio="A" * 10,
            interview_insights=["A" * 501],
        )
    assert "is too long" in str(exc.value)

    # Bad characters
    with pytest.raises(ValidationError) as exc:
        Persona(
            name="A" * 10,
            occupation="A" * 10,
            demographics="A" * 10,
            goals=["A" * 10],
            frustrations=["A" * 10],
            bio="A" * 10,
            interview_insights=["Valid insight with a quote 'bad'"],
        )
    assert "contains invalid characters" in str(exc.value)


def test_politics_matrix_edges() -> None:
    from src.domain_models.politics import InfluenceNetwork, SparseMatrixEntry, Stakeholder

    s1 = Stakeholder(name="A", initial_support=0.5, stubbornness=0.5)
    s2 = Stakeholder(name="B", initial_support=0.5, stubbornness=0.5)

    # Matrix values out of bounds in dense matrix
    with pytest.raises(ValidationError) as exc:
        InfluenceNetwork(stakeholders=[s1, s2], matrix=[[1.5, -0.5], [0.5, 0.5]])
    assert "Matrix values must be between 0.0 and 1.0" in str(
        exc.value
    ) or "Input should be less than or equal to 1" in str(exc.value)

    # Non-square dense matrix
    with pytest.raises(ValidationError) as exc:
        InfluenceNetwork(stakeholders=[s1, s2], matrix=[[0.5, 0.5]])
    assert "Matrix dimensions do not match stakeholder count" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        InfluenceNetwork(stakeholders=[s1, s2], matrix=[[0.5], [0.5]])
    assert "Matrix shape is invalid" in str(exc.value)

    # Sparse matrix shape mismatch
    with pytest.raises(ValidationError) as exc:
        InfluenceNetwork(stakeholders=[s1, s2], matrix=[SparseMatrixEntry(row=0, col=2, val=1.0)])
    assert "Matrix shape is invalid" in str(exc.value)

    # Sparse matrix stochasticity failure
    with pytest.raises(ValidationError) as exc:
        InfluenceNetwork(stakeholders=[s1, s2], matrix=[SparseMatrixEntry(row=0, col=0, val=0.5)])
    assert "Influence matrix rows must sum to 1.0" in str(exc.value)


def test_state_wrap_iterator_edges() -> None:
    from src.domain_models.common import LazyIdeaIterator
    from src.domain_models.lean_canvas import LeanCanvas
    from src.domain_models.state import GlobalState

    with pytest.raises(TypeError) as exc_type:
        GlobalState(generated_ideas="not an iterator")
    assert "must be an Iterator" in str(exc_type.value)

    # Wrap an existing LazyIdeaIterator
    def gen() -> Iterator[LeanCanvas]:
        yield LeanCanvas(
            id=1,
            title="A" * 10,
            problem="A b c",
            customer_segments="devs",
            unique_value_prop="A b c",
            solution="A b c",
        )

    lazy_iter = LazyIdeaIterator(gen())
    state = GlobalState(generated_ideas=lazy_iter)
    assert state.generated_ideas is lazy_iter


def test_transcript_date_edges() -> None:
    from src.domain_models.transcript import Transcript

    with pytest.raises(ValidationError) as exc:
        Transcript(source="User", content="Valid content that is long enough", date="2024/01/01")
    assert "Date must be in YYYY-MM-DD format" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        Transcript(source="User", content="too short", date="2024-01-01")
    assert "Transcript content is too short" in str(exc.value)

    # Duplicate sources
    from src.domain_models.state import GlobalState

    with pytest.raises(ValidationError) as exc:
        GlobalState(
            transcripts=[
                Transcript(
                    source="User", content="Valid content that is long enough", date="2024-01-01"
                ),
                Transcript(source="User", content="Another valid content here", date="2024-01-02"),
            ]
        )
    assert "Duplicate transcript sources found" in str(exc.value)

    # Transcript too long
    with pytest.raises(ValidationError) as exc:
        GlobalState(transcripts=[Transcript(source="User", content="A" * 50001, date="2024-01-01")])
    assert "exceeds maximum length" in str(exc.value)


def test_coverage_gap_fillers() -> None:
    # MVP component ascii check
    from src.domain_models.mvp import MVPSpec

    with pytest.raises(ValidationError) as exc:
        MVPSpec(app_name="App", core_feature="A" * 10, components=["非ASCII"])
    assert "must be ASCII" in str(exc.value)

    # common.py Iterator wrapping CoreSchema

    from src.domain_models.common import LazyIdeaIterator

    schema = LazyIdeaIterator.__get_pydantic_core_schema__(None, None)
    assert schema["type"] == "is-instance"

    # politics.py sparse matrix checks
    from src.domain_models.politics import InfluenceNetwork, SparseMatrixEntry, Stakeholder

    s1 = Stakeholder(name="A", initial_support=0.5, stubbornness=0.5)
    s2 = Stakeholder(name="B", initial_support=0.5, stubbornness=0.5)

    with pytest.raises(ValidationError) as exc:
        InfluenceNetwork(stakeholders=[s1, s2], matrix=[SparseMatrixEntry(row=0, col=2, val=1.0)])
    assert "Matrix shape is invalid" in str(exc.value)

    with pytest.raises(ValidationError) as exc:
        InfluenceNetwork(stakeholders=[s1, s2], matrix=[SparseMatrixEntry(row=0, col=0, val=0.5)])
    assert "Influence matrix rows must sum to 1.0" in str(exc.value)

    # State duplicate transcripts and invalid iterator wrapping
    from src.domain_models.state import GlobalState

    with pytest.raises(ValidationError) as exc:
        GlobalState.model_validate(
            {
                "transcripts": [
                    {"source": "X", "content": "Valid length content here", "date": "2024-01-01"},
                    {"source": "X", "content": "Another valid length here", "date": "2024-01-02"},
                ]
            }
        )
    assert "Duplicate transcript sources found" in str(exc.value)

    with pytest.raises(TypeError) as exc_type:
        GlobalState(generated_ideas=123)
    assert "must be an Iterator" in str(exc_type.value)
