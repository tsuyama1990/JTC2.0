import os
from unittest.mock import MagicMock, patch

import pytest

from src.agents.governance import GovernanceAgent
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.metrics import Metrics, RingiSho
from src.domain_models.mvp import MVP, Feature, MVPType, Priority
from src.domain_models.state import GlobalState


@patch.dict(os.environ, {"OPENAI_API_KEY": "sk-dummy", "TAVILY_API_KEY": "tv-dummy"})
class TestCycle06UAT:
    @pytest.fixture
    def initial_state(self) -> GlobalState:
        return GlobalState(
            topic="UAT Cycle 6",
            metrics_data=Metrics(),
            mvp_definition=MVP(
                type=MVPType.SINGLE_FEATURE,
                core_features=[Feature(name="AI Summarizer", description="Summarizes text", priority=Priority.MUST_HAVE)],
                success_criteria="User saves time",
                v0_url="https://v0.dev/uat-result"
            ),
            selected_idea=LeanCanvas(
                id=1,
                title="UAT App",
                problem="Problem is definitely big enough.",
                solution="Solution is scalable.",
                customer_segments="B2B, Enterprise.",
                unique_value_prop="AI-driven solution for enterprises.",
            )
        )

    def test_uat_c06_01_financial_viability(self, initial_state: GlobalState) -> None:
        """
        Scenario 1: Financial Viability Check
        Verify that the system calculates financials and flags unviable business models.
        """
        agent = GovernanceAgent()

        # Define mock inputs
        mock_cac = 500.0
        mock_arpu = 20.0
        mock_churn = 0.05

        # Calculate expected derived values based on logic in src/core/metrics.py
        # LTV = ARPU / Churn
        expected_ltv = mock_arpu / mock_churn # 400.0
        # ROI = LTV / CAC
        expected_roi = expected_ltv / mock_cac # 0.8

        # Mock dependencies
        with patch("src.agents.governance.TavilySearch") as mock_search_cls:
             mock_search = mock_search_cls.return_value
             mock_search.safe_search.return_value = "Search result"

             with patch("src.agents.governance.get_llm") as mock_llm_factory, \
                  patch("src.agents.governance.GovernanceAgent._save_to_file"):
                 mock_llm = mock_llm_factory.return_value

                 # Mock 2 LLM calls with streaming
                 chunk_fin = MagicMock()
                 chunk_fin.content = f'{{"cac": {mock_cac}, "arpu": {mock_arpu}, "churn_rate": {mock_churn}}}'

                 chunk_ringi = MagicMock()
                 chunk_ringi.content = '{"title": "Proposal", "executive_summary": "Bad idea.", "risks": ["High churn"]}'

                 # stream returns iterator
                 mock_llm.stream.side_effect = [iter([chunk_fin]), iter([chunk_ringi])]

                 # Run agent
                 result = agent.run(initial_state)

                 # Verify RingiSho created
                 if "ringi_sho" in result:
                     ringi_sho = result["ringi_sho"]
                     assert isinstance(ringi_sho, RingiSho)
                     assert ringi_sho.approval_status == "Rejected"

                     # Verify mathematical correctness dynamically
                     # Use approximate assertion for float comparison
                     assert abs(ringi_sho.financial_projection.ltv - expected_ltv) < 0.01
                     assert abs(ringi_sho.financial_projection.roi - expected_roi) < 0.01
                 else:
                     pytest.fail("RingiSho not generated")

    def test_uat_c06_02_ringi_sho_generation(self, initial_state: GlobalState) -> None:
        """
        Scenario 2: Ringi-sho Generation
        Verify generation of the final approval document.
        """
        agent = GovernanceAgent()

        # Define mock inputs for SUCCESS case
        mock_cac = 600.0
        mock_arpu = 100.0
        mock_churn = 0.02

        # Expected
        expected_ltv = mock_arpu / mock_churn # 5000.0
        expected_roi = expected_ltv / mock_cac # 8.33...

        with patch("src.agents.governance.TavilySearch") as mock_search_cls:
             mock_search = mock_search_cls.return_value
             mock_search.safe_search.return_value = "Search result"

             with patch("src.agents.governance.get_llm") as mock_llm_factory, \
                  patch("src.agents.governance.GovernanceAgent._save_to_file"):
                 mock_llm = mock_llm_factory.return_value

                 chunk_fin = MagicMock()
                 chunk_fin.content = f'{{"cac": {mock_cac}, "arpu": {mock_arpu}, "churn_rate": {mock_churn}}}'

                 chunk_ringi = MagicMock()
                 chunk_ringi.content = '{"title": "Proposal", "executive_summary": "Great idea.", "risks": ["None"]}'

                 mock_llm.stream.side_effect = [iter([chunk_fin]), iter([chunk_ringi])]

                 result = agent.run(initial_state)

                 if "ringi_sho" in result:
                     ringi_sho = result["ringi_sho"]
                     assert ringi_sho.approval_status == "Approved"
                     assert abs(ringi_sho.financial_projection.ltv - expected_ltv) < 0.01
                     assert abs(ringi_sho.financial_projection.roi - expected_roi) < 0.01
                 else:
                     pytest.fail("RingiSho not generated")
