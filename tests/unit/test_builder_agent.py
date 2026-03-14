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
    with patch("src.agents.builder.ChatOpenAI", autospec=True) as mock:
        yield mock.return_value


@pytest.fixture
def agent(mock_llm: MagicMock) -> BuilderAgent:
<<<<<<< HEAD
    with patch("src.agents.builder.get_settings"):
=======
    with patch("src.agents.builder.get_settings") as mock_settings:
>>>>>>> dbf79509e5301d6b0cbef8dc6782ab30464bee9e
        return BuilderAgent(llm=mock_llm)


@pytest.fixture
def state_with_context() -> GlobalState:
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
    )


class TestBuilderAgent:
    def test_compile_context_with_idea(
        self, agent: BuilderAgent, state_with_context: GlobalState
    ) -> None:
        """Test _compile_context correctly stringifies models."""
        context = agent._compile_context(state_with_context)
        assert "Idea: App title" in context
        assert "Problem: Prob is a big problem" in context
        assert "Solution: Sol is the best solution" in context

    def test_compile_context_empty(self, agent: BuilderAgent) -> None:
        """Test _compile_context handles empty state."""
        state = GlobalState(topic="Test")
        context = agent._compile_context(state)
        assert context == ""

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

<<<<<<< HEAD
        # Create a mock object, not mocking the method itself which type checkers dislike
        mock_llm_structured = MagicMock()
        mock_llm_structured.return_value = mock_chain
        agent.llm.with_structured_output = mock_llm_structured  # type: ignore
=======
        agent.llm.with_structured_output.return_value = mock_chain
>>>>>>> dbf79509e5301d6b0cbef8dc6782ab30464bee9e

        result = agent._generate_agent_prompt_spec("Context")
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

<<<<<<< HEAD
        mock_llm_structured = MagicMock()
        mock_llm_structured.return_value = mock_chain
        agent.llm.with_structured_output = mock_llm_structured  # type: ignore
=======
        agent.llm.with_structured_output.return_value = mock_chain
>>>>>>> dbf79509e5301d6b0cbef8dc6782ab30464bee9e

        result = agent._generate_experiment_plan("Context")
        assert result == expected_plan

    def test_run_empty_context(self, agent: BuilderAgent) -> None:
        """Test run aborts if there's no context available."""
        state = GlobalState(topic="test")
        result = agent.run(state)
        assert result == {}

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
            assert result == {}
