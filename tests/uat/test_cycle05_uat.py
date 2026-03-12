import os
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest

from src.core.config import get_settings
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.mvp import MVPSpec
from src.domain_models.state import GlobalState
from tests.conftest import DUMMY_ENV_VARS

# We import the real V0Client to mock its internals, not the class itself if possible
try:
    from src.agents.builder import BuilderAgent
    from src.tools.v0_client import V0Client
except ImportError:
    BuilderAgent = None  # type: ignore
    V0Client = None  # type: ignore


class TestCycle05UAT:
    @pytest.fixture(autouse=True)
    def patch_env(self) -> Iterator[None]:
        """Apply env patching at the fixture level instead of class level."""
        with patch.dict(os.environ, DUMMY_ENV_VARS):
            yield
    def test_uat_c05_00_config_loading(self) -> None:
        """
        Verify get_settings() behavior with missing configuration.
        """
        if BuilderAgent is None:
            pytest.skip("BuilderAgent not implemented")

        get_settings.cache_clear()

        # Test missing v0 API key behavior in BuilderAgent
        # Using get_settings directly to avoid Settings import errors in tests
        mock_settings = get_settings()

        # Deep copy or store original to restore later
        original_v0 = mock_settings.v0_api_key
        mock_settings.v0_api_key = None

        try:
            with (
                patch("src.agents.builder.get_settings", return_value=mock_settings),
                pytest.raises(ValueError, match="Missing required API configuration")
            ):
                BuilderAgent(llm=MagicMock())
        finally:
            mock_settings.v0_api_key = original_v0

        get_settings.cache_clear()

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
        with patch.object(
            agent,
            "_extract_features",
            return_value=iter(["Feature 1 desc", "Feature 2 desc", "Feature 3 desc"]),
        ):
            result = agent.propose_features(initial_state)

            assert "candidate_features" in result
            features = list(result["candidate_features"])
            assert len(features) == 3
            assert "mvp_url" not in result  # Should NOT generate yet

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

        mock_settings = get_settings()
        original_v0 = mock_settings.v0_api_key
        mock_secret = MagicMock()
        mock_secret.get_secret_value.return_value = "test-key"
        mock_settings.v0_api_key = mock_secret

        try:
            with patch("src.agents.builder.get_settings", return_value=mock_settings):
                agent = BuilderAgent(llm=mock_llm)
        finally:
            mock_settings.v0_api_key = original_v0

        # Mock Spec Creation to return a valid spec
        with (
            patch.object(
                agent,
                "_create_mvp_spec",
                return_value=MVPSpec(
                    app_name="UAT App",
                    core_feature="Feature 2 desc",
                    components=["Hero"],
                    v0_prompt="Generate UI",
                ),
            ),
            patch("src.tools.v0_client.httpx.Client") as mock_http_cls,
        ):
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
        Simulate API failure and test V0Client directly.
        """
        # Import directly to avoid unbound local error
        try:
            from src.agents.builder import BuilderAgent
            from src.core.exceptions import V0GenerationError
            from src.tools.v0_client import V0Client
        except ImportError:
            pytest.skip("BuilderAgent or V0Client not implemented")

        # 1. Test V0Client directly to satisfy Security rule about not just mocking httpx
        # Initialize client with mock settings to prevent pybreaker from complaining about missing settings inside it

        mock_settings = get_settings()
        original_v0_api_key = mock_settings.v0_api_key

        mock_secret = MagicMock()
        mock_secret.get_secret_value.return_value = "test-key"
        mock_settings.v0_api_key = mock_secret

        import httpx

        def mock_handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(500, text="Internal Server Error")

        mock_transport = httpx.MockTransport(mock_handler)

        try:
            with patch("src.tools.v0_client.get_settings", return_value=mock_settings):
                client = V0Client(api_key="test-key")

                # Since V0Client uses "with httpx.Client(...) as client", we mock the __enter__ directly to yield our native client
                native_client = httpx.Client(transport=mock_transport)
                mock_client_ctx = MagicMock()
                mock_client_ctx.__enter__.return_value = native_client

                with (
                    patch("src.tools.v0_client.httpx.Client", return_value=mock_client_ctx),
                    pytest.raises(V0GenerationError, match="V0 generation failed")
                ):
                    client.generate_ui("test prompt")

            # 2. Test Agent error propagation
            initial_state.selected_feature = "Feature 1"
            mock_llm = MagicMock()

            with patch("src.agents.builder.get_settings", return_value=mock_settings):
                agent = BuilderAgent(llm=mock_llm)

            # Ensure Feature string meets length validation (>10 chars)
            long_feature = "Feature 1 must be very long indeed"

            with (
                patch.object(
                    agent,
                    "_create_mvp_spec",
                    return_value=MVPSpec(app_name="App", core_feature=long_feature, components=[]),
                ),
                patch("src.agents.builder.V0Client") as MockV0Client,
            ):
                # We know the agent throws a RuntimeError wrapping whatever exception V0Client raises.
                mock_client_instance = MockV0Client.return_value
                mock_client_instance.generate_ui.side_effect = V0GenerationError("Mocked failure")

                with pytest.raises(
                    (RuntimeError, V0GenerationError),
                    match="Feature extraction failed|V0 API generation failed|Mocked failure"
                ):
                    agent.generate_mvp(initial_state)
        finally:
            mock_settings.v0_api_key = original_v0_api_key
