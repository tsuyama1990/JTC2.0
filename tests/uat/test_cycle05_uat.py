import os
from unittest.mock import MagicMock, patch

import pytest

from src.core.config import get_settings
from src.core.exceptions import V0GenerationError
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.mvp import MVPSpec
from src.domain_models.state import GlobalState
from tests.conftest import DUMMY_ENV_VARS

# We import the real V0Client to mock its internals, not the class itself if possible
try:
    from src.agents.builder import BuilderAgent
    from src.tools.v0_client import V0Client
except ImportError:
    BuilderAgent = None
    V0Client = None # type: ignore

@patch.dict(os.environ, DUMMY_ENV_VARS)
class TestCycle05UAT:
    @pytest.fixture
    def initial_state(self) -> GlobalState:
        return GlobalState(
            topic="UAT Cycle 5",
            selected_idea=LeanCanvas(
                id=1,
                title="UAT App",
                problem="Problem is definitely big enough.",
                solution="Feature 1 description, Feature 2 description, Feature 3 description",
                customer_segments="Segments are defined.",
                unique_value_prop="UVP is also defined.",
            ),
        )

    def test_uat_c05_01_feature_pruning(self, initial_state: GlobalState) -> None:
        """
        Scenario 1: Feature Pruning
        Verify that the system forces selection of a single feature.
        """
        if BuilderAgent is None:
            pytest.skip("BuilderAgent not implemented")

        get_settings.cache_clear()

        # 1. Run Builder Agent (First Pass)
        mock_llm = MagicMock()
        agent = BuilderAgent(llm=mock_llm)

        # Mock the internal LLM call for extraction
        with patch.object(agent, "_extract_features", return_value=["Feature 1 desc", "Feature 2 desc", "Feature 3 desc"]):
            result = agent.propose_features(initial_state)

            assert "candidate_features" in result
            assert len(result["candidate_features"]) == 3
            assert "mvp_url" not in result # Should NOT generate yet

    def test_uat_c05_02_mvp_generation_integration(self, initial_state: GlobalState) -> None:
        """
        Scenario 2: MVP Generation Integration
        Verify v0.dev call after selection, mocking at the network level (httpx) rather than the client class.
        """
        if BuilderAgent is None or V0Client is None:
            pytest.skip("Components not available")

        get_settings.cache_clear()

        # Setup state with selection
        initial_state.candidate_features = ["Feature 1 desc", "Feature 2 desc", "Feature 3 desc"]
        initial_state.selected_feature = "Feature 2 desc"

        mock_llm = MagicMock()
        agent = BuilderAgent(llm=mock_llm)

        # Mock Spec Creation to return a valid spec
        with patch.object(agent, "_create_mvp_spec", return_value=MVPSpec(
            app_name="UAT App",
            core_feature="Feature 2 desc",
            components=["Hero"],
            v0_prompt="Generate UI"
        )):
            # Mock httpx in V0Client to simulate real API interaction
            with patch("src.tools.v0_client.httpx.Client") as mock_http_cls:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"url": "https://v0.dev/uat-result"}

                mock_client_instance = mock_http_cls.return_value.__enter__.return_value
                mock_client_instance.post.return_value = mock_response

                # Execute
                result = agent.generate_mvp(initial_state)

                assert result["mvp_url"] == "https://v0.dev/uat-result"
                assert result["mvp_spec"].core_feature == "Feature 2 desc"

                # Verify network call was made
                mock_client_instance.post.assert_called_once()

    def test_uat_c05_03_error_handling(self, initial_state: GlobalState) -> None:
        """
        Scenario 3: Error Handling
        Simulate API failure.
        """
        if BuilderAgent is None:
            pytest.skip("BuilderAgent not implemented")

        initial_state.selected_feature = "Feature 1"
        mock_llm = MagicMock()
        agent = BuilderAgent(llm=mock_llm)

        # Ensure Feature string meets length validation (>10 chars)
        long_feature = "Feature 1 must be very long indeed"

        with patch.object(agent, "_create_mvp_spec", return_value=MVPSpec(
            app_name="App", core_feature=long_feature, components=[]
        )), patch("src.tools.v0_client.httpx.Client") as mock_http_cls:
           mock_response = MagicMock()
           mock_response.status_code = 500
           mock_response.text = "Internal Server Error"

           mock_client_instance = mock_http_cls.return_value.__enter__.return_value
           mock_client_instance.post.return_value = mock_response

           # Should handle V0GenerationError internally or expose it?
           # The agent catches exceptions? Let's check agent implementation.
           # Actually agent.generate_mvp raises V0GenerationError?
           # Safe node wrapper handles it. But here we test agent directly.

           with pytest.raises(V0GenerationError):
               agent.generate_mvp(initial_state)
