from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from src.agents.builder import FeatureList
from src.core.config import get_settings
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.mvp import MVPSpec
from src.domain_models.state import GlobalState

try:
    from src.agents.builder import BuilderAgent
except ImportError:
    BuilderAgent = None  # type: ignore


class TestBuilderAgent:
    @pytest.fixture
    def state_with_idea(self) -> GlobalState:
        return GlobalState(
            topic="Test Topic",
            selected_idea=LeanCanvas(
                id=1,
                title="Test App",
                problem="Problem is strictly big enough.",
                solution="Feature A long description, Feature B long description, Feature C long description",
                customer_segments="Users segment is defined.",
                unique_value_prop="Value proposition is clear.",
            ),
        )

    @pytest.fixture
    def agent(self) -> BuilderAgent:
        if BuilderAgent is None:
            pytest.skip("BuilderAgent not implemented")
        # Mock LLM
        mock_llm = MagicMock()
        return BuilderAgent(llm=mock_llm)

    def test_extract_features_real_call(self, agent: BuilderAgent) -> None:
        """
        Test _extract_features with mocked LLM response.
        Ensures the chain invoke is mocked properly to be deterministic.
        """
        # Mock the specific chain construction in the method
        with patch("src.agents.builder.ChatPromptTemplate.from_messages") as mock_prompt:
            mock_prompt_tmpl = MagicMock()
            mock_prompt.return_value = mock_prompt_tmpl

            mock_model_runnable = MagicMock()
            mock_llm = cast(MagicMock, agent.llm)
            mock_llm.with_structured_output.return_value = mock_model_runnable

            mock_chain = MagicMock()
            mock_prompt_tmpl.__or__.return_value = mock_chain

            # Mock the invoke result
            mock_chain.invoke.return_value = FeatureList(features=["F1", "F2"])

            # Execute with input long enough to pass short-check
            input_text = "solution that is sufficiently long to pass the length validation check"
            features = list(agent._extract_features(input_text))

            assert features == ["F1", "F2"]
            # Verify invocation happened
            mock_chain.invoke.assert_called()

    def test_extract_features_error_handling(self, agent: BuilderAgent) -> None:
        """Test _extract_features handles exceptions and raises RuntimeError."""
        with patch("src.agents.builder.ChatPromptTemplate.from_messages") as mock_prompt:
            mock_prompt_tmpl = MagicMock()
            mock_prompt.return_value = mock_prompt_tmpl

            mock_model_runnable = MagicMock()
            mock_llm = cast(MagicMock, agent.llm)
            mock_llm.with_structured_output.return_value = mock_model_runnable

            mock_chain = MagicMock()
            mock_prompt_tmpl.__or__.return_value = mock_chain

            # Simulate exception
            mock_chain.invoke.side_effect = Exception("Mock LLM failure")

            input_text = "solution that is sufficiently long to pass the length validation check"

            with pytest.raises(RuntimeError, match="Feature extraction failed"):
                list(agent._extract_features(input_text))

    def test_extract_features_non_featurelist(self, agent: BuilderAgent) -> None:
        """Test _extract_features handles unexpected output type."""
        with patch("src.agents.builder.ChatPromptTemplate.from_messages") as mock_prompt:
            mock_prompt_tmpl = MagicMock()
            mock_prompt.return_value = mock_prompt_tmpl

            mock_model_runnable = MagicMock()
            mock_llm = cast(MagicMock, agent.llm)
            mock_llm.with_structured_output.return_value = mock_model_runnable

            mock_chain = MagicMock()
            mock_prompt_tmpl.__or__.return_value = mock_chain

            # Return unexpected object
            mock_chain.invoke.return_value = {"features": ["F1"]}

            input_text = "solution that is sufficiently long to pass the length validation check"

            features = list(agent._extract_features(input_text))
            assert features == []  # Should safely skip if not FeatureList

    @patch("src.agents.builder.ChatPromptTemplate.from_messages")
    def test_create_mvp_spec_success(self, mock_prompt: MagicMock, agent: BuilderAgent) -> None:
        """Test _create_mvp_spec returns MVPSpec correctly."""
        # Using sys.modules to inject a dummy module for src.core.prompts
        import sys
        import types

        if "src.core.prompts" not in sys.modules:
            dummy_module = types.ModuleType("src.core.prompts")
            dummy_module.PROMPT_MVP_SPEC_SYSTEM = "system"  # type: ignore
            dummy_module.PROMPT_MVP_SPEC_USER = "user {app_name} {feature} {idea_context}"  # type: ignore
            sys.modules["src.core.prompts"] = dummy_module

        mock_prompt_tmpl = MagicMock()
        mock_prompt.return_value = mock_prompt_tmpl

        mock_model_runnable = MagicMock()
        mock_llm = cast(MagicMock, agent.llm)
        mock_llm.with_structured_output.return_value = mock_model_runnable

        mock_chain = MagicMock()
        mock_prompt_tmpl.__or__.return_value = mock_chain

        expected_spec = MVPSpec(
            app_name="App",
            core_feature="Feature A long enough",
            components=["Hero"],
        )
        mock_chain.invoke.return_value = expected_spec

        result = agent._create_mvp_spec(
            "App", "Feature A long enough", "Context Context Context Context Context"
        )
        assert result == expected_spec

    @patch("src.agents.builder.ChatPromptTemplate.from_messages")
    def test_create_mvp_spec_fallback_exception(
        self, mock_prompt: MagicMock, agent: BuilderAgent
    ) -> None:
        """Test _create_mvp_spec fallback when exception occurs."""
        import sys
        import types

        if "src.core.prompts" not in sys.modules:
            dummy_module = types.ModuleType("src.core.prompts")
            dummy_module.PROMPT_MVP_SPEC_SYSTEM = "system"  # type: ignore
            dummy_module.PROMPT_MVP_SPEC_USER = "user {app_name} {feature} {idea_context}"  # type: ignore
            sys.modules["src.core.prompts"] = dummy_module

        mock_prompt_tmpl = MagicMock()
        mock_prompt.return_value = mock_prompt_tmpl

        mock_model_runnable = MagicMock()
        mock_llm = cast(MagicMock, agent.llm)
        mock_llm.with_structured_output.return_value = mock_model_runnable

        mock_chain = MagicMock()
        mock_prompt_tmpl.__or__.return_value = mock_chain
        mock_chain.invoke.side_effect = Exception("Failed")

        result = agent._create_mvp_spec("App", "Feature A long enough", "Context")

        # Should return default spec
        assert result.app_name == "App"
        assert result.core_feature == "Feature A long enough"

    @patch("src.agents.builder.ChatPromptTemplate.from_messages")
    def test_create_mvp_spec_fallback_wrong_type(
        self, mock_prompt: MagicMock, agent: BuilderAgent
    ) -> None:
        """Test _create_mvp_spec fallback when incorrect type returned."""
        import sys
        import types

        if "src.core.prompts" not in sys.modules:
            dummy_module = types.ModuleType("src.core.prompts")
            dummy_module.PROMPT_MVP_SPEC_SYSTEM = "system"  # type: ignore
            dummy_module.PROMPT_MVP_SPEC_USER = "user {app_name} {feature} {idea_context}"  # type: ignore
            sys.modules["src.core.prompts"] = dummy_module

        mock_prompt_tmpl = MagicMock()
        mock_prompt.return_value = mock_prompt_tmpl

        mock_model_runnable = MagicMock()
        mock_llm = cast(MagicMock, agent.llm)
        mock_llm.with_structured_output.return_value = mock_model_runnable

        mock_chain = MagicMock()
        mock_prompt_tmpl.__or__.return_value = mock_chain
        mock_chain.invoke.return_value = {"wrong": "type"}

        result = agent._create_mvp_spec("App", "Feature A long enough", "Context")

        assert isinstance(result, MVPSpec)
        assert result.app_name == "App"
        assert result.core_feature == "Feature A long enough"

    def test_propose_features_no_idea(self, agent: BuilderAgent) -> None:
        """Test propose_features gracefully handles missing idea."""
        state = GlobalState(topic="Test")
        result = agent.propose_features(state)
        assert result == {}

    def test_propose_features_with_existing_candidates(
        self, agent: BuilderAgent, state_with_idea: GlobalState
    ) -> None:
        """Test propose_features correctly uses existing candidate features."""
        state_with_idea.candidate_features = ["Feature A"]
        result = agent.propose_features(state_with_idea)
        assert result == {"candidate_features": ["Feature A"]}

    def test_propose_features_empty_extraction(
        self, agent: BuilderAgent, state_with_idea: GlobalState
    ) -> None:
        """Test propose_features handles when no features are extracted."""
        with patch.object(agent, "_extract_features", return_value=iter([])):
            result = agent.propose_features(state_with_idea)
            assert "candidate_features" in result
            assert list(result["candidate_features"]) == []

    def test_generate_mvp_no_idea(self, agent: BuilderAgent) -> None:
        """Test generate_mvp handles missing idea."""
        state = GlobalState(topic="Test")
        result = agent.generate_mvp(state)
        assert result == {}

    def test_generate_mvp_no_feature(
        self, agent: BuilderAgent, state_with_idea: GlobalState
    ) -> None:
        """Test generate_mvp handles missing selected_feature with empty candidates."""
        state_with_idea.candidate_features = []
        result = agent.generate_mvp(state_with_idea)
        assert result == {}

    def test_generate_mvp_missing_api_key(
        self, agent: BuilderAgent, state_with_idea: GlobalState
    ) -> None:
        """Test generate_mvp raises ValueError if API key is missing."""
        state_with_idea.selected_feature = "Feature A"

        # Override setting manually
        mock_settings = get_settings()
        original = mock_settings.v0_api_key

        # We need to simulate the key missing right before the check
        try:
            mock_settings.v0_api_key = None  # type: ignore
            agent.settings = mock_settings

            with (
                patch.object(
                    agent,
                    "_create_mvp_spec",
                    return_value=MVPSpec(
                        app_name="A", core_feature="Feature A that is long enough"
                    ),
                ),
                pytest.raises(ValueError, match="V0 API Key is missing. Cannot generate UI."),
            ):
                agent.generate_mvp(state_with_idea)
        finally:
            mock_settings.v0_api_key = original

    def test_generate_mvp_exception_propagation(
        self, agent: BuilderAgent, state_with_idea: GlobalState
    ) -> None:
        """Test generate_mvp propagates exceptions from V0Client."""
        state_with_idea.selected_feature = "Feature A"

        with (
            patch.object(
                agent,
                "_create_mvp_spec",
                return_value=MVPSpec(app_name="A", core_feature="Feature A that is long enough"),
            ),
            patch("src.agents.builder.V0Client") as mock_v0,
        ):
            mock_client = MagicMock()
            mock_client.generate_ui.side_effect = Exception("API error")
            mock_v0.return_value = mock_client

            with pytest.raises(Exception, match="API error"):
                agent.generate_mvp(state_with_idea)

    def test_run_no_idea(self, agent: BuilderAgent) -> None:
        """Test run with no idea."""
        state = GlobalState(topic="test")
        result = agent.run(state)
        assert result == {}

    def test_run_propose(self, agent: BuilderAgent, state_with_idea: GlobalState) -> None:
        """Test run defers to propose_features when no feature selected."""
        with patch.object(
            agent, "propose_features", return_value={"candidate_features": ["F1"]}
        ) as mock_propose:
            result = agent.run(state_with_idea)
            assert result == {"candidate_features": ["F1"]}
            mock_propose.assert_called_once()

    def test_run_generate(self, agent: BuilderAgent, state_with_idea: GlobalState) -> None:
        """Test run defers to generate_mvp when feature is selected."""
        state_with_idea.selected_feature = "F1"
        with patch.object(agent, "generate_mvp", return_value={"mvp_url": "url"}) as mock_gen:
            result = agent.run(state_with_idea)
            assert result == {"mvp_url": "url"}
            mock_gen.assert_called_once()

    def test_run_exception(self, agent: BuilderAgent, state_with_idea: GlobalState) -> None:
        """Test run catches exception and returns empty dict."""
        state_with_idea.selected_feature = "F1"
        with patch.object(agent, "generate_mvp", side_effect=Exception("Failed")):
            result = agent.run(state_with_idea)
            assert result == {}
