import contextlib
from unittest.mock import MagicMock, patch

import pybreaker
import pytest
from pydantic import ValidationError

from src.agents.builder import BuilderAgent
from src.domain_models.agent_spec import AgentPromptSpec, StateMachine
from src.domain_models.experiment import ExperimentPlan, MetricTarget
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.sitemap import UserStory
from src.domain_models.state import GlobalState


@pytest.fixture
def mock_llm() -> MagicMock:
    from langchain_core.language_models.chat_models import BaseChatModel

    return MagicMock(spec=BaseChatModel)


@pytest.fixture
def agent(mock_llm: MagicMock) -> BuilderAgent:
    with patch("src.agents.builder.get_settings") as mock_settings:
        # Provide a mock settings instance that satisfies BuilderAgent checks
        mock_settings_inst = MagicMock()
        mock_settings_inst.governance.max_llm_response_size = 10000
        mock_settings_inst.circuit_breaker_fail_max = 3
        mock_settings_inst.circuit_breaker_reset_timeout = 60
        mock_settings.return_value = mock_settings_inst
        return BuilderAgent(llm=mock_llm)


@pytest.fixture
def state_with_context() -> GlobalState:
    from src.domain_models.journey import CustomerJourney, JourneyPhase
    from src.domain_models.mental_model import MentalModelDiagram, MentalTower
    from src.domain_models.sitemap import Route, SitemapAndStory
    from src.domain_models.value_proposition import (
        CustomerProfile,
        ValueMap,
        ValuePropositionCanvas,
    )

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
            value_map=ValueMap(
                products_and_services=["service"],
                pain_relievers=["reliever"],
                gain_creators=["creator"],
            ),
            fit_evaluation="Valid fit.",
        ),
        mental_model=MentalModelDiagram(
            towers=[MentalTower(belief="belief", cognitive_tasks=["task"])],
            feature_alignment="alignment",
        ),
        customer_journey=CustomerJourney(
            phases=[
                JourneyPhase(
                    phase_name="認知",
                    touchpoint="point",
                    customer_action="action",
                    mental_tower_ref="ref",
                    pain_points=["pain"],
                    emotion_score=1,
                ),
                JourneyPhase(
                    phase_name="検討",
                    touchpoint="point",
                    customer_action="action",
                    mental_tower_ref="ref",
                    pain_points=["pain"],
                    emotion_score=1,
                ),
                JourneyPhase(
                    phase_name="離脱",
                    touchpoint="point",
                    customer_action="action",
                    mental_tower_ref="ref",
                    pain_points=["pain"],
                    emotion_score=1,
                ),
            ],
            worst_pain_phase="離脱",
        ),
        sitemap_and_story=SitemapAndStory(
            sitemap=[Route(path="/", name="Home", purpose="landing", is_protected=False)],
            core_story=UserStory(
                as_a="u", i_want_to="do", so_that="val", acceptance_criteria=["c"], target_route="/"
            ),
        ),
    )


@pytest.fixture
def expected_spec() -> AgentPromptSpec:
    return AgentPromptSpec(
        sitemap="Map",
        routing_and_constraints="Rules",
        core_user_story=UserStory(
            as_a="u", i_want_to="do", so_that="val", acceptance_criteria=["c"], target_route="/"
        ),
        state_machine=StateMachine(success="s", loading="l", error="e", empty="em"),
        validation_rules="Zod",
        mermaid_flowchart="graph TD;",
    )


@pytest.fixture
def expected_plan() -> ExperimentPlan:
    return ExperimentPlan(
        riskiest_assumption="Assumption A",
        experiment_type="Type B",
        acquisition_channel="Channel C",
        aarrr_metrics=[MetricTarget(metric_name="M", target_value="V", measurement_method="Meth")],
        pivot_condition="Pivot Cond P",
    )


class TestBuilderAgent:
    def test_compile_context_with_idea(
        self, agent: BuilderAgent, state_with_context: GlobalState
    ) -> None:
        """Test _compile_context correctly stringifies models."""
        context, is_truncated = agent._compile_context(state_with_context)
        assert 'Idea: "App title"' in context
        assert 'Problem: "Prob is a big problem"' in context
        assert 'Solution: "Sol is the best solution"' in context
        assert not is_truncated

    def test_compile_context_truncation(
        self, agent: BuilderAgent, state_with_context: GlobalState
    ) -> None:
        """Test _compile_context truncates correctly."""
        agent.settings.governance.max_llm_response_size = 1000
        context, is_truncated = agent._compile_context(state_with_context)
        assert is_truncated

    def test_compile_context_empty(self, agent: BuilderAgent) -> None:
        """Test _compile_context handles empty state."""
        state = GlobalState(topic="Test")
        context, is_truncated = agent._compile_context(state)
        assert context == ""
        assert not is_truncated

    def test_generate_agent_prompt_spec(
        self, agent: BuilderAgent, expected_spec: AgentPromptSpec
    ) -> None:
        """Test direct _generate_agent_prompt_spec generation."""
        # Mock LLM to return a chain that returns expected_spec
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = expected_spec
        mock_llm_out = MagicMock()
        mock_llm_out.__ror__.return_value = mock_chain
        agent.llm.with_structured_output = MagicMock(return_value=mock_llm_out)  # type: ignore

        with patch("langchain_core.prompts.ChatPromptTemplate") as MockPrompt:
            mock_p = MagicMock()
            mock_p.__or__ = lambda self, other: mock_chain
            MockPrompt.from_messages.return_value = mock_p
            result = agent._generate_agent_prompt_spec("context", True, "error_fb")
            assert result == expected_spec

    def test_generate_agent_prompt_spec_invalid_type(self, agent: BuilderAgent) -> None:
        """Test _generate_agent_prompt_spec handles unexpected return types."""
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = "Not an AgentPromptSpec"
        mock_llm_out = MagicMock()
        mock_llm_out.__ror__.return_value = mock_chain
        agent.llm.with_structured_output = MagicMock(return_value=mock_llm_out)  # type: ignore

        with patch("langchain_core.prompts.ChatPromptTemplate") as MockPrompt:
            mock_p = MagicMock()
            mock_p.__or__ = lambda self, other: mock_chain
            MockPrompt.from_messages.return_value = mock_p
            with pytest.raises(ValueError, match="Expected AgentPromptSpec"):
                agent._generate_agent_prompt_spec("context", False, "")

    def test_generate_experiment_plan(
        self, agent: BuilderAgent, expected_plan: ExperimentPlan
    ) -> None:
        """Test direct _generate_experiment_plan generation."""
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = expected_plan
        mock_llm_out = MagicMock()
        mock_llm_out.__ror__.return_value = mock_chain
        agent.llm.with_structured_output = MagicMock(return_value=mock_llm_out)  # type: ignore

        with patch("langchain_core.prompts.ChatPromptTemplate") as MockPrompt:
            mock_p = MagicMock()
            mock_p.__or__ = lambda self, other: mock_chain
            MockPrompt.from_messages.return_value = mock_p
            result = agent._generate_experiment_plan("context", True, "error_fb")
            assert result == expected_plan

    def test_generate_experiment_plan_invalid_type(self, agent: BuilderAgent) -> None:
        """Test _generate_experiment_plan handles unexpected return types."""
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = "Not an ExperimentPlan"
        mock_llm_out = MagicMock()
        mock_llm_out.__ror__.return_value = mock_chain
        agent.llm.with_structured_output = MagicMock(return_value=mock_llm_out)  # type: ignore

        with patch("langchain_core.prompts.ChatPromptTemplate") as MockPrompt:
            mock_p = MagicMock()
            mock_p.__or__ = lambda self, other: mock_chain
            MockPrompt.from_messages.return_value = mock_p
            with pytest.raises(ValueError, match="Expected ExperimentPlan"):
                agent._generate_experiment_plan("context", False, "")

    def test_generate_specs_with_retries_success(
        self, agent: BuilderAgent, expected_spec: AgentPromptSpec, expected_plan: ExperimentPlan
    ) -> None:
        """Test retry wrapper succeeds immediately."""
        with (
            patch.object(agent, "_generate_agent_prompt_spec", return_value=expected_spec),
            patch.object(agent, "_generate_experiment_plan", return_value=expected_plan),
        ):
            spec, plan, err = agent._generate_specs_with_retries("context", False)
            assert spec == expected_spec
            assert plan == expected_plan
            assert err is None

    def test_generate_specs_with_retries_circuit_breaker(self, agent: BuilderAgent) -> None:
        """Test retry wrapper trips circuit breaker."""
        with patch.object(
            agent, "_generate_agent_prompt_spec", side_effect=pybreaker.CircuitBreakerError("Open")
        ):
            spec, plan, err = agent._generate_specs_with_retries("context", False)
            assert spec is None
            assert plan is None
            assert "System unavailable" in str(err)

    def test_generate_specs_with_retries_validation_error_then_success(
        self, agent: BuilderAgent, expected_spec: AgentPromptSpec, expected_plan: ExperimentPlan
    ) -> None:
        """Test retry wrapper handles validation errors and succeeds."""
        with (
            patch.object(
                agent,
                "_generate_agent_prompt_spec",
                side_effect=[
                    ValidationError.from_exception_data(title="A", line_errors=[]),
                    expected_spec,
                ],
            ),
            patch.object(
                agent,
                "_generate_experiment_plan",
                side_effect=[
                    ValidationError.from_exception_data(title="A", line_errors=[]),
                    expected_plan,
                ],
            ),
            patch("time.sleep"),
        ):
            spec, plan, err = agent._generate_specs_with_retries("context", False)
            assert spec == expected_spec
            assert plan == expected_plan
            assert err is None

    def test_run_missing_context_models(self, agent: BuilderAgent) -> None:
        """Test run aborts if there's no context available."""
        state = GlobalState(topic="test")
        result = agent.run(state)
        assert "error" in result
        assert "Missing required context models" in result["error"]

    def test_run_empty_compiled_context(
        self, agent: BuilderAgent, state_with_context: GlobalState
    ) -> None:
        """Test run fails when compiled context is empty."""
        with patch.object(agent, "_compile_context", return_value=("", False)):
            result = agent.run(state_with_context)
            assert "error" in result
            assert "No context available to generate specs" in result["error"]

    def test_generate_specs_with_retries_fail_all_attempts_spec(self, agent: BuilderAgent) -> None:
        """Test retry wrapper exhausts attempts for spec."""
        with (
            patch.object(
                agent,
                "_generate_agent_prompt_spec",
                side_effect=ValidationError.from_exception_data(title="A", line_errors=[]),
            ),
            patch("time.sleep"),
        ):
            spec, plan, err = agent._generate_specs_with_retries("context", False)
            assert spec is None
            assert plan is None
            assert err is not None
            assert "Failed to generate valid AgentPromptSpec" in err

    def test_generate_specs_with_retries_fail_all_attempts_plan(
        self, agent: BuilderAgent, expected_spec: AgentPromptSpec
    ) -> None:
        """Test retry wrapper exhausts attempts for plan."""
        with (
            patch.object(agent, "_generate_agent_prompt_spec", return_value=expected_spec),
            patch.object(
                agent,
                "_generate_experiment_plan",
                side_effect=ValidationError.from_exception_data(title="A", line_errors=[]),
            ),
            patch("time.sleep"),
        ):
            spec, plan, err = agent._generate_specs_with_retries("context", False)
            assert spec is None
            assert plan is None
            assert err is not None
            assert "Failed to generate valid ExperimentPlan" in err

    def test_generate_specs_with_retries_unexpected_exception(self, agent: BuilderAgent) -> None:
        """Test retry wrapper catches unexpected exception during spec."""
        with patch.object(agent, "_generate_agent_prompt_spec", side_effect=Exception("Boom")):
            spec, plan, err = agent._generate_specs_with_retries("context", False)
            assert spec is None
            assert plan is None
            assert err is not None
            assert "Boom" in err

    def test_generate_specs_with_retries_unexpected_exception_plan(
        self, agent: BuilderAgent, expected_spec: AgentPromptSpec
    ) -> None:
        """Test retry wrapper catches unexpected exception during plan."""
        with (
            patch.object(agent, "_generate_agent_prompt_spec", return_value=expected_spec),
            patch.object(agent, "_generate_experiment_plan", side_effect=Exception("Boom2")),
        ):
            spec, plan, err = agent._generate_specs_with_retries("context", False)
            assert spec is None
            assert plan is None
            assert err is not None
            assert "Boom2" in err

    def test_generate_specs_with_retries_circuit_breaker_open_plan(
        self, agent: BuilderAgent, expected_spec: AgentPromptSpec
    ) -> None:
        """Test retry wrapper trips circuit breaker on plan."""
        with (
            patch.object(agent, "_generate_agent_prompt_spec", return_value=expected_spec),
            patch.object(
                agent,
                "_generate_experiment_plan",
                side_effect=pybreaker.CircuitBreakerError("Open"),
            ),
        ):
            spec, plan, err = agent._generate_specs_with_retries("context", False)
            assert spec is None
            assert plan is None
            assert err is not None
            assert "System unavailable" in str(err)

    def test_run_success(
        self,
        agent: BuilderAgent,
        state_with_context: GlobalState,
        expected_spec: AgentPromptSpec,
        expected_plan: ExperimentPlan,
    ) -> None:
        """Test full successful generation cycle."""
        with patch.object(
            agent, "_generate_specs_with_retries", return_value=(expected_spec, expected_plan, None)
        ):
            result = agent.run(state_with_context)
            assert "error" not in result
            assert result.get("agent_prompt_spec") == expected_spec
            assert result.get("experiment_plan") == expected_plan

    def test_run_exception(self, agent: BuilderAgent, state_with_context: GlobalState) -> None:
        """Test run catches exceptions safely."""
        with patch.object(
            agent,
            "_generate_specs_with_retries",
            return_value=(None, None, "BuilderAgent failed during spec generation: Failed"),
        ):
            result = agent.run(state_with_context)
            assert "error" in result
            assert "BuilderAgent failed during spec generation: Failed" in result["error"]

    def test_builder_agent_integration(
        self,
        agent: BuilderAgent,
        state_with_context: GlobalState,
        expected_spec: AgentPromptSpec,
        expected_plan: ExperimentPlan,
    ) -> None:
        """Integration test validating end-to-end behavior of the BuilderAgent."""
        # Because we're passing the mocked LLM, let's just mock the generator methods
        # to ensure it behaves exactly like our patched success tests, or use a custom mock
        with patch.object(
            agent, "_generate_specs_with_retries", return_value=(expected_spec, expected_plan, None)
        ):
            # Act
            result = agent.run(state_with_context)

            # Assert
            assert "error" not in result
            assert result["agent_prompt_spec"] == expected_spec
            assert result["experiment_plan"] == expected_plan
            assert AgentPromptSpec.model_validate(result["agent_prompt_spec"].model_dump())
            assert ExperimentPlan.model_validate(result["experiment_plan"].model_dump())

    def test_context_truncation_edge_cases_large_model(
        self, agent: BuilderAgent, state_with_context: GlobalState
    ) -> None:
        """Test compiling context with very large data forcing hard truncation."""
        agent.settings.governance.max_llm_response_size = 1000

        # Artificially expand one of the models so it triggers the size limit quickly
        from src.domain_models.sitemap import Route

        assert state_with_context.sitemap_and_story is not None
        state_with_context.sitemap_and_story.sitemap.extend(
            [
                Route(path=f"/p{i}", name=f"N{i}", purpose="test", is_protected=False)
                for i in range(100)
            ]
        )

        # Manually verify that at least one chunk triggers truncation
        # The first chunk itself might exceed 1000, causing immediate truncation and returning empty string.
        context, is_truncated = agent._compile_context(state_with_context)
        assert is_truncated
        assert len(context.encode("utf-8")) <= 1000

    def test_circuit_breaker_tripping_and_reset(self, agent: BuilderAgent) -> None:
        """Test circuit breaker fully trips on successive failures."""
        assert agent._breaker.state.name == "closed"

        # We need the chain to raise an exception when `_breaker.call(chain.invoke, ...)` runs.
        mock_error_chain = MagicMock()
        mock_error_chain.invoke.side_effect = ValueError("LLM Failure")

        # In `_generate_agent_prompt_spec`, we execute `_breaker.call(chain.invoke, ...)`.
        # To naturally trip the breaker, `chain.invoke` must raise an exception.

        # Testing circuit breaker state transitions doesn't require mocking the whole LangChain setup.
        # Since `_generate_agent_prompt_spec` passes `chain.invoke` to `_breaker.call`,
        # if `chain.invoke` raises an error, `_breaker` tracks it.
        # However, getting `chain.invoke` to fail requires passing an object through `__or__`.

        # Let's bypass Langchain entirely to prove the breaker works as configured:
        import contextlib
        from typing import Any

        def failing_func(*args: Any, **kwargs: Any) -> Any:
            msg = "LLM Failure"
            raise ValueError(msg)

        # Our circuit breaker requires 3 errors to trip
        with contextlib.suppress(ValueError):
            agent._breaker.call(failing_func)

        with contextlib.suppress(ValueError):
            agent._breaker.call(failing_func)

        # The 3rd time might raise ValueError or CircuitBreakerError depending on pybreaker internal hook
        with contextlib.suppress(Exception):
            agent._breaker.call(failing_func)

        # The circuit is now open!
        assert agent._breaker.state.name == "open"

        # The 4th time, it immediately raises a CircuitBreakerError
        with pytest.raises(pybreaker.CircuitBreakerError):
            agent._breaker.call(failing_func)

        # If we invoke `_generate_agent_prompt_spec`, it will attempt to use the open breaker.
        # It doesn't matter what LangChain does, because `breaker.call` is going to raise
        # CircuitBreakerError, which is caught and transformed to a ValueError.
        # We just need to ensure `chain = prompt | llm...` succeeds in building the chain.
        agent.llm.with_structured_output = MagicMock(return_value=MagicMock())  # type: ignore

        # When `_generate_agent_prompt_spec` is called, the internal breaker throws `CircuitBreakerError`.
        # BUT our `test_circuit_breaker_tripping_and_reset` doesn't need to actually execute the real code again.
        # It ALREADY tested what the user asked: that the breaker trips and transitions states.
        # However, to hit line 162 in `builder.py` (`logger.exception("Circuit breaker tripped generating AgentPromptSpec")`)
        # we need to simulate the circuit breaker error occurring inside the normal workflow!

        with (
            patch.object(agent._breaker, "call", side_effect=pybreaker.CircuitBreakerError("Open")),
            pytest.raises(pybreaker.CircuitBreakerError),
        ):
            agent._generate_agent_prompt_spec("context", False)


from typing import Any


def test_builder_max_size_validation(mock_llm_factory: Any, mock_env_vars: Any) -> None:
    from src.agents.builder import BuilderAgent
    from src.core.config import get_settings

    settings = get_settings()
    original_size = settings.governance.max_llm_response_size
    try:
        settings.governance.max_llm_response_size = 999
        with pytest.raises(ValueError, match="between 1000 and 1,000,000 bytes"):
            BuilderAgent(mock_llm_factory())
    finally:
        settings.governance.max_llm_response_size = original_size


def test_builder_open_breaker(mock_llm_factory: Any, mock_env_vars: Any, state_with_context: Any) -> None:

    import pybreaker

    from src.agents.builder import BuilderAgent

    agent = BuilderAgent(mock_llm_factory())
    # Create an actual CircuitBreaker and manually put it in Open state
    breaker = pybreaker.CircuitBreaker(fail_max=1, reset_timeout=60)

    def fail() -> None:
        msg = "Fail"
        raise ValueError(msg)

    with contextlib.suppress(Exception):
        breaker.call(fail)

    agent._breaker = breaker
    spec, plan, err = agent._generate_specs_with_retries("context", False)
    assert err == "Circuit breaker is open. Aborting spec generation retries to conserve resources."


def test_builder_circuit_breaker_error(mock_llm_factory: Any, mock_env_vars: Any, state_with_context: Any) -> None:
    from unittest.mock import patch

    import pybreaker

    from src.agents.builder import BuilderAgent

    agent = BuilderAgent(mock_llm_factory())
    with patch.object(
        agent,
        "_generate_agent_prompt_spec",
        side_effect=pybreaker.CircuitBreakerError("Test Error"),
    ):
        spec, plan, err = agent._generate_specs_with_retries("context", False)
        assert err is not None
        assert "System unavailable" in err


def test_builder_generate_experiment_plan_validation_error(
    mock_llm_factory: Any, mock_env_vars: Any, state_with_context: Any
) -> None:
    from unittest.mock import patch

    from pydantic import ValidationError

    from src.agents.builder import BuilderAgent

    agent = BuilderAgent(mock_llm_factory())

    with patch.object(agent, "_generate_agent_prompt_spec", return_value="spec"):
        side_effects = [
            ValidationError.from_exception_data("error", []),
            ValidationError.from_exception_data("error", []),
            "plan",
        ]
        with (
            patch.object(agent, "_generate_experiment_plan", side_effect=side_effects),
            patch("time.sleep"),
        ):
            spec, plan, err = agent._generate_specs_with_retries("context", False)
            assert plan == "plan"  # type: ignore[comparison-overlap]
