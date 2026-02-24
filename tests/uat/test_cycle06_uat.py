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

        # Mock dependencies
        with patch("src.agents.governance.TavilySearch") as mock_search_cls:
             mock_search = mock_search_cls.return_value
             mock_search.safe_search.return_value = "CAC: $500\nChurn: 5%\nARPU: $20"

             # Mock LLM generation for RingiSho to include "Rejected" or "Approved"
             with patch("src.agents.governance.get_llm") as mock_llm_factory, \
                  patch("src.agents.governance.GovernanceAgent._save_to_file"):
                 mock_llm = mock_llm_factory.return_value

                 # Mock 2 LLM calls: 1. Financials, 2. RingiSho
                 # We return realistic but unviable numbers for this scenario
                 # LTV = 20 / 0.05 = 400. ROI = 400 / 500 = 0.8 (< 3.0 threshold)
                 mock_msg_fin = MagicMock()
                 mock_msg_fin.content = '{"cac": 500.0, "arpu": 20.0, "churn_rate": 0.05}'

                 mock_msg_ringi = MagicMock()
                 mock_msg_ringi.content = '{"title": "Proposal", "executive_summary": "Bad idea.", "risks": ["High churn"]}'

                 mock_llm.invoke.side_effect = [mock_msg_fin, mock_msg_ringi]

                 # Run agent
                 result = agent.run(initial_state)

                 # Verify RingiSho created
                 # Note: Implementation logic will put it in result dict or update state
                 if "ringi_sho" in result:
                     ringi_sho = result["ringi_sho"]
                     assert isinstance(ringi_sho, RingiSho)
                     assert ringi_sho.approval_status == "Rejected"
                     # Verify ACTUAL calculation logic was used
                     # LTV = 20 / 0.05 = 400. ROI = 400 / 500 = 0.8
                     assert ringi_sho.financial_projection.ltv == 400.0
                     assert ringi_sho.financial_projection.roi == 0.8
                 else:
                     # Fail explicitly if logic not implemented (TDD)
                     pytest.fail("RingiSho not generated")

    def test_uat_c06_02_ringi_sho_generation(self, initial_state: GlobalState) -> None:
        """
        Scenario 2: Ringi-sho Generation
        Verify generation of the final approval document.
        """
        agent = GovernanceAgent()

        # Mock dependencies for SUCCESS case
        with patch("src.agents.governance.TavilySearch") as mock_search_cls:
             mock_search = mock_search_cls.return_value
             mock_search.safe_search.return_value = "CAC: $600\nChurn: 2%\nARPU: $100"

             with patch("src.agents.governance.get_llm") as mock_llm_factory, \
                  patch("src.agents.governance.GovernanceAgent._save_to_file"):
                 mock_llm = mock_llm_factory.return_value

                 # Mock 2 LLM calls
                 # LTV = 100 / 0.02 = 5000. ROI = 5000 / 600 = 8.33
                 mock_msg_fin = MagicMock()
                 mock_msg_fin.content = '{"cac": 600.0, "arpu": 100.0, "churn_rate": 0.02}'

                 mock_msg_ringi = MagicMock()
                 mock_msg_ringi.content = '{"title": "Proposal", "executive_summary": "Great idea.", "risks": ["None"]}'

                 mock_llm.invoke.side_effect = [mock_msg_fin, mock_msg_ringi]

                 result = agent.run(initial_state)

                 if "ringi_sho" in result:
                     ringi_sho = result["ringi_sho"]
                     assert ringi_sho.approval_status == "Approved"
                     # LTV = 100 / 0.02 = 5000. ROI = 5000 / 600 = 8.333
                     assert ringi_sho.financial_projection.ltv == 5000.0
                     assert ringi_sho.financial_projection.roi > 8.0
                 else:
                     pytest.fail("RingiSho not generated")
