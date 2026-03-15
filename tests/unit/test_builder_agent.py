from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

from src.agents.builder import BuilderAgent
from src.domain_models.agent_spec import AgentPromptSpec, StateMachine
from src.domain_models.experiment import ExperimentPlan, MetricTarget
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.sitemap import UserStory
from src.domain_models.state import GlobalState


@pytest.fixture
def mock_llm() -> Generator[MagicMock, None, None]:
    with patch("src.agents.builder.BaseChatModel", autospec=True) as mock:
        yield mock.return_value


@pytest.fixture
def agent(mock_llm: MagicMock) -> BuilderAgent:
    with patch("src.agents.builder.get_settings") as mock_settings:
        # Mock settings used in BuilderAgent
        mock_settings_inst = MagicMock()
        mock_settings_inst.circuit_breaker_fail_max = 3
        mock_settings_inst.circuit_breaker_reset_timeout = 60
        mock_settings_inst.governance.max_llm_response_size = 10000
        mock_settings.return_value = mock_settings_inst
        return BuilderAgent(llm=mock_llm)


@pytest.fixture
def state_with_context() -> GlobalState:
    from src.domain_models.value_proposition import ValuePropositionCanvas, CustomerProfile, ValueMap
    from src.domain_models.mental_model import MentalModelDiagram, MentalTower
    from src.domain_models.journey import CustomerJourney, JourneyPhase
    from src.domain_models.sitemap import SitemapAndStory, Route

    return GlobalState(
        topic="Testing",
        selected_idea=LeanCanvas(
            id=1,
            title="App title",
            problem="Prob is a big problem",
            customer_segments="Seg",
            unique_value_prop="Val is a great prop",
            solution="Sol is the best solution",
            status="draft",
        ),
        vpc=ValuePropositionCanvas(
            customer_profile=CustomerProfile(customer_jobs=["job"], pains=["pain"], gains=["gain"]),
            value_map=ValueMap(products_and_services=["service"], pain_relievers=["reliever"], gain_creators=["creator"]),
            fit_evaluation="Valid fit."
        ),
        mental_model=MentalModelDiagram(
            towers=[MentalTower(belief="belief", cognitive_tasks=["task"])],
            feature_alignment="alignment"
        ),
        customer_journey=CustomerJourney(
            phases=[
                JourneyPhase(phase_name="認知", touchpoint="point", customer_action="action", mental_tower_ref="ref", pain_points=["pain"], emotion_score=1),
                JourneyPhase(phase_name="検討", touchpoint="point", customer_action="action", mental_tower_ref="ref", pain_points=["pain"], emotion_score=1),
                JourneyPhase(phase_name="離脱", touchpoint="point", customer_action="action", mental_tower_ref="ref", pain_points=["pain"], emotion_score=1)
            ],
            worst_pain_phase="離脱"
        ),
        sitemap_and_story=SitemapAndStory(
            sitemap=[Route(path="/", name="Home", purpose="landing", is_protected=False)],
            core_story=UserStory(as_a="u", i_want_to="do", so_that="val", acceptance_criteria=["c"], target_route="/")
        )
    )


class TestBuilderAgent:
    def test_compile_context_with_idea(
        self, agent: BuilderAgent, state_with_context: GlobalState
    ) -> None:
        """Test _compile_context correctly stringifies models."""
        context, is_truncated = agent._compile_context(state_with_context)
        assert "Idea: App title" in context
        assert "Problem: Prob is a big problem" in context
        assert "Solution: Sol is the best solution" in context
        assert not is_truncated

    def test_compile_context_empty(self, agent: BuilderAgent) -> None:
        """Test _compile_context handles empty state."""
        state = GlobalState(topic="Test")
        context, is_truncated = agent._compile_context(state)
        assert context == ""
        assert not is_truncated

    @patch("src.agents.builder.ChatPromptTemplate.from_messages")
    def test_generate_agent_prompt_spec_success(
        self, mock_prompt: MagicMock, agent: BuilderAgent
    ) -> None:
        """Test generating AgentPromptSpec successfully."""
        mock_prompt_tmpl = MagicMock()
        mock_prompt.return_value = mock_prompt_tmpl

        expected_spec = AgentPromptSpec(
            sitemap="Map",
            routing_and_constraints="Rules",
            core_user_story=UserStory(
                as_a="u", i_want_to="do", so_that="val", acceptance_criteria=["c"], target_route="/"
            ),
            state_machine=StateMachine(success="s", loading="l", error="e", empty="em"),
            validation_rules="Zod",
            mermaid_flowchart="graph TD;",
        )

        mock_chain = MagicMock()
        mock_chain.invoke.return_value = expected_spec
        mock_prompt_tmpl.__or__.return_value = mock_chain

        mock_llm_structured = MagicMock()
        mock_llm_structured.return_value = mock_chain
        agent.llm.with_structured_output = mock_llm_structured  # type: ignore

        result = agent._generate_agent_prompt_spec("Context", False)
        assert result == expected_spec

    @patch("src.agents.builder.ChatPromptTemplate.from_messages")
    def test_generate_experiment_plan_success(
        self, mock_prompt: MagicMock, agent: BuilderAgent
    ) -> None:
        """Test generating ExperimentPlan successfully."""
        mock_prompt_tmpl = MagicMock()
        mock_prompt.return_value = mock_prompt_tmpl

        expected_plan = ExperimentPlan(
            riskiest_assumption="Assumption A",
            experiment_type="Type B",
            acquisition_channel="Channel C",
            aarrr_metrics=[
                MetricTarget(metric_name="M", target_value="V", measurement_method="Meth")
            ],
            pivot_condition="Pivot Cond P",
        )

        mock_chain = MagicMock()
        mock_chain.invoke.return_value = expected_plan
        mock_prompt_tmpl.__or__.return_value = mock_chain

        mock_llm_structured = MagicMock()
        mock_llm_structured.return_value = mock_chain
        agent.llm.with_structured_output = mock_llm_structured  # type: ignore

        result = agent._generate_experiment_plan("Context", False)
        assert result == expected_plan

    def test_run_empty_context(self, agent: BuilderAgent) -> None:
        """Test run aborts if there's no context available."""
        state = GlobalState(topic="test")
        result = agent.run(state)
        assert "error" in result

    def test_run_success(self, agent: BuilderAgent, state_with_context: GlobalState) -> None:
        """Test full successful generation cycle."""
        expected_spec = AgentPromptSpec(
            sitemap="Map",
            routing_and_constraints="Rules",
            core_user_story=UserStory(
                as_a="u", i_want_to="do", so_that="val", acceptance_criteria=["c"], target_route="/"
            ),
            state_machine=StateMachine(success="s", loading="l", error="e", empty="em"),
            validation_rules="Zod",
            mermaid_flowchart="graph TD;",
        )
        expected_plan = ExperimentPlan(
            riskiest_assumption="Assumption A",
            experiment_type="Type B",
            acquisition_channel="Channel C",
            aarrr_metrics=[
                MetricTarget(metric_name="M", target_value="V", measurement_method="Meth")
            ],
            pivot_condition="Pivot Cond P",
        )

        with (
            patch.object(agent, "_generate_agent_prompt_spec", return_value=expected_spec),
            patch.object(agent, "_generate_experiment_plan", return_value=expected_plan),
        ):
            result = agent.run(state_with_context)
            assert result == {
                "agent_prompt_spec": expected_spec,
                "experiment_plan": expected_plan,
            }

    def test_run_exception(self, agent: BuilderAgent, state_with_context: GlobalState) -> None:
        """Test run catches exceptions safely."""
        with patch.object(agent, "_generate_agent_prompt_spec", side_effect=Exception("Failed")):
            result = agent.run(state_with_context)
            assert "error" in result
