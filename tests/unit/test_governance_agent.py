from unittest.mock import MagicMock, patch

import pytest

from src.agents.governance import GovernanceAgent
from src.domain_models.agent_spec import AgentPromptSpec, StateMachine
from src.domain_models.experiment import ExperimentPlan, MetricTarget
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.metrics import Metrics
from src.domain_models.sitemap import UserStory
from src.domain_models.state import GlobalState


class TestGovernanceAgent:
    @pytest.fixture
    def mock_state(self) -> GlobalState:
        """Create a mock GlobalState."""
        state = GlobalState()
        state.topic = "AI Productivity Tool"
        state.metrics_data = Metrics()
        state.agent_prompt_spec = AgentPromptSpec(
            sitemap="a",
            routing_and_constraints="b",
            core_user_story=UserStory(
                as_a="c", i_want_to="d", so_that="e", acceptance_criteria=["f"], target_route="/g"
            ),
            state_machine=StateMachine(success="h", loading="i", error="j", empty="k"),
            validation_rules="l",
            mermaid_flowchart="m",
        )
        state.experiment_plan = ExperimentPlan(
            riskiest_assumption="Assumption A",
            experiment_type="Type B",
            acquisition_channel="Channel C",
            aarrr_metrics=[
                MetricTarget(metric_name="M", target_value="V", measurement_method="Meth")
            ],
            pivot_condition="Pivot Cond P",
        )
        return state

    def test_get_industry_context(self) -> None:
        """Test industry context extraction."""
        agent = GovernanceAgent()

        state = GlobalState(topic="Test Topic")
        assert agent._get_industry_context(state) == "Test Topic"

        state.selected_idea = LeanCanvas(
            id=1,
            title="A is a good title",
            problem="B is a big problem",
            customer_segments="Doctors",
            unique_value_prop="C is very unique value prop",
            solution="D is the best solution",
        )
        assert agent._get_industry_context(state) == "Doctors related to Test Topic"

    @patch("src.agents.governance.get_llm")
    def test_estimate_financials_success(self, mock_get_llm: MagicMock) -> None:
        """Test successful financial estimation."""
        agent = GovernanceAgent()
        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm

        # stream returns an iterator of chunks
        chunk = MagicMock()
        chunk.content = '```json\n{"cac": 100.0, "arpu": 10.0, "churn_rate": 0.05}\n```'
        mock_llm.stream.return_value = iter([chunk])

        result = agent._estimate_financials("Health", "Search data")

        assert result.cac == 100.0
        assert result.ltv == 10.0 / 0.05  # 200.0
        assert result.payback_months == 100.0 / 10.0  # 10.0
        assert result.roi == 200.0 / 100.0  # 2.0

    @patch("src.agents.governance.get_llm")
    def test_estimate_financials_fallback(self, mock_get_llm: MagicMock) -> None:
        """Test fallback to defaults if estimation fails."""
        agent = GovernanceAgent()
        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm

        # Trigger JSONDecodeError
        chunk = MagicMock()
        chunk.content = "Invalid JSON"
        mock_llm.stream.return_value = iter([chunk])

        with patch("src.agents.governance.get_settings") as mock_settings_func:
            mock_settings = mock_settings_func.return_value
            mock_settings.governance.default_cac = 50.0
            mock_settings.governance.default_arpu = 5.0
            mock_settings.governance.default_churn = 0.1
            mock_settings.governance.max_llm_response_size = 1000

            result = agent._estimate_financials("Health", "Search data")

            assert result.cac == 50.0
            assert result.ltv == 5.0 / 0.1  # 50.0
