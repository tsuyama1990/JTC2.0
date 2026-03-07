from unittest.mock import MagicMock, patch

import pytest

from src.agents.governance import GovernanceAgent
from src.core.services.file_service import FileService
from src.domain_models.metrics import Metrics
from src.domain_models.mvp import MVP, Feature, MVPType, Priority
from src.domain_models.politics import InfluenceNetwork, Stakeholder
from src.domain_models.state import GlobalState


class TestGovernanceAgent:
    """Test suite for Governance Agent."""

    @pytest.fixture
    def mock_state(self) -> GlobalState:
        """Create a mock GlobalState."""
        state = GlobalState()
        state.topic = "AI Productivity Tool"
        state.metrics_data = Metrics()
        state.mvp_definition = MVP(
            type=MVPType.SINGLE_FEATURE,
            core_features=[
                Feature(
                    name="AI Summarizer", description="Summarizes text", priority=Priority.MUST_HAVE
                )
            ],
            success_criteria="User saves time",
        )
        state.influence_network = InfluenceNetwork(
            stakeholders=[Stakeholder(name="CEO", initial_support=0.8, stubbornness=0.1)],
            matrix=[[1.0]],
        )
        return state

    @patch("src.agents.governance.TavilySearch")
    @patch("src.core.metrics.calculate_ltv")
    @patch("src.core.metrics.calculate_payback_period")
    @patch("src.core.metrics.calculate_roi")
    def test_run_populates_ringi_sho(
        self,
        mock_roi: MagicMock,
        mock_payback: MagicMock,
        mock_ltv: MagicMock,
        mock_search_cls: MagicMock,
        mock_state: GlobalState,
    ) -> None:
        """Test that run method populates RingiSho in the returned dictionary."""
        # Setup mocks
        mock_search_instance = mock_search_cls.return_value
        mock_search_instance.safe_search.return_value = "CAC: $500\nChurn: 5%\nARPU: $100"

        mock_ltv.return_value = 2000.0
        mock_payback.return_value = 5.0
        mock_roi.return_value = 4.0

        # Mock File Service
        mock_file_service = MagicMock(spec=FileService)

        agent = GovernanceAgent(file_service=mock_file_service)

        # Check `src/core/llm.py` later. For now, let's assume it runs.

        with patch("src.agents.governance.get_llm") as mock_llm_factory:
            mock_llm = mock_llm_factory.return_value

            # Mock LLM responses (called twice: financials, then ringi-sho)
            # Use stream instead of invoke because the agent uses stream for memory safety
            mock_chunk_fin = MagicMock()
            mock_chunk_fin.content = '{"cac": 500.0, "arpu": 100.0, "churn_rate": 0.05}'

            mock_chunk_ringi = MagicMock()
            mock_chunk_ringi.content = (
                '{"title": "AI Tool", "executive_summary": "Great tool.", "risks": ["Risk 1"]}'
            )

            # stream returns an iterator. We simulate it with a list.
            mock_llm.stream.side_effect = [[mock_chunk_fin], [mock_chunk_ringi]]

            result = agent.run(mock_state)

            # Expectation: RingiSho and metrics populated
            assert isinstance(result, dict)
            assert "ringi_sho" in result
            assert "metrics_data" in result

            # Verify FileService call
            mock_file_service.save_text_async.assert_called_once()
            args, _ = mock_file_service.save_text_async.call_args
            assert "# AI Tool" in args[0]  # Verify content
