from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from src.agents.governance import GovernanceAgent
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

    @patch("src.core.llm.LLMFactory.get_llm")
    def test_safe_llm_call_rejects_large_response(
        self, mock_llm_factory: MagicMock, agent: GovernanceAgent
    ) -> None:
        """Verify that _safe_llm_call raises ValueError for oversized responses."""
        mock_llm = mock_llm_factory.return_value

        # Mock streaming response
        # Create chunks that sum up to > limit
        # Limit set to 10 bytes for testing

        chunk1 = MagicMock()
        chunk1.content = "12345"
        chunk2 = MagicMock()
        chunk2.content = "678901"  # Total 11 chars

        # Use settings factory to create isolated settings with a low limit
        from src.core.config import Settings

        # Avoid global patches, configure test-specific settings locally to the agent
        test_settings = Settings(
            OPENAI_API_KEY="sk-12345678901234567890", TAVILY_API_KEY="tvly-12345678901234567890"
        )
        test_settings.governance.max_llm_response_size = 10
        agent.settings = test_settings  # type: ignore[attr-defined]

        # Inject directly into agent
        agent.llm = mock_llm  # type: ignore[attr-defined]

        # mock_llm is the Client instance. We mock the stream method.
        mock_llm.stream.return_value = iter([chunk1, chunk2])

        # Pydantic 2.x throws ValidationError if model is incorrectly mocked,
        # but in this case, we expect it to hit the size limit FIRST and raise ValueError.
        with pytest.raises(ValueError, match=ERR_LLM_RESPONSE_TOO_LARGE):
            agent._safe_llm_call("prompt", DummyModel)

    @patch("src.agents.governance.TavilySearch")
    def test_search_result_truncation(
        self, mock_search_cls: MagicMock, agent: GovernanceAgent
    ) -> None:
        """Verify search results are truncated before processing."""
        from src.core.config import SettingsFactory
        settings = SettingsFactory().build()
        limit = settings.governance.max_search_result_size

        # Create a search result larger than the limit
        large_result = "A" * (limit + 1000)

        mock_search = mock_search_cls.return_value
        mock_search.safe_search.return_value = large_result

        state = GlobalState(topic="Test")

        # Return a valid object so run() doesn't crash on property access
        mock_financials = MagicMock()
        mock_financials.roi = 5.0

        with (
            patch.object(
                agent, "_estimate_financials", return_value=mock_financials
            ) as mock_estimate,
            patch.object(agent, "_generate_ringi_sho"),
            patch.object(agent, "_save_to_file"),
        ):
            agent.run(state)

            # Check arguments passed to _estimate_financials
            args, _ = mock_estimate.call_args
            passed_search_result = args[1]

            assert len(passed_search_result) == limit
            assert passed_search_result == "A" * limit
