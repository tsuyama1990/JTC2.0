from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from src.agents.governance import GovernanceAgent
from src.core.config import get_settings
from src.core.constants import ERR_LLM_RESPONSE_TOO_LARGE
from src.core.services.file_service import FileService
from src.domain_models.state import GlobalState


class DummyModel(BaseModel):
    value: str


class TestGovernanceMemorySafety:
    """Tests specifically for memory safety and large input handling."""

    @pytest.fixture
    def agent(self) -> GovernanceAgent:
        return GovernanceAgent(file_service=MagicMock(spec=FileService))

    @patch("src.agents.governance.get_llm")
    def test_safe_llm_call_rejects_large_response(self, mock_llm_factory: MagicMock, agent: GovernanceAgent) -> None:
        """Verify that _safe_llm_call raises ValueError for oversized responses."""
        mock_llm = mock_llm_factory.return_value

        # Configure a small limit for testing
        settings = get_settings()
        original_limit = settings.governance.max_llm_response_size

        # Patch the settings object instance directly
        with patch.object(settings.governance, "max_llm_response_size", 10):
            # Return a response larger than 10 bytes
            mock_llm.invoke.return_value.content = '{"value": "This is too long"}'

            with pytest.raises(ValueError, match=ERR_LLM_RESPONSE_TOO_LARGE):
                agent._safe_llm_call("prompt", DummyModel)

    @patch("src.agents.governance.TavilySearch")
    def test_search_result_truncation(self, mock_search_cls: MagicMock, agent: GovernanceAgent) -> None:
        """Verify search results are truncated before processing."""
        settings = get_settings()
        limit = settings.governance.max_search_result_size

        # Create a search result larger than the limit
        large_result = "A" * (limit + 1000)

        mock_search = mock_search_cls.return_value
        mock_search.safe_search.return_value = large_result

        state = GlobalState(topic="Test")

        # We need to mock _estimate_financials because it's called inside run
        # We want to verify it receives the truncated string
        # BUT we also need to return a valid Financials object (or mock) because `run` uses `financials.roi` immediately after

        mock_financials = MagicMock()
        mock_financials.roi = 5.0 # Ensure it's a float for comparison

        with patch.object(agent, "_estimate_financials", return_value=mock_financials) as mock_estimate:
            # Mock other calls to prevent full execution
            with patch.object(agent, "_generate_ringi_sho"), patch.object(agent, "_save_to_file"):
                agent.run(state)

                # Check arguments passed to _estimate_financials
                args, _ = mock_estimate.call_args
                # args[0] is industry, args[1] is search_result
                passed_search_result = args[1]

                assert len(passed_search_result) == limit
                assert passed_search_result == "A" * limit
