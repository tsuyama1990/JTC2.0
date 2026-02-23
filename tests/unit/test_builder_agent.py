from unittest.mock import MagicMock, patch

import pytest

from src.agents.builder import FeatureList
from src.core.exceptions import V0GenerationError
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.mvp import MVPSpec
from src.domain_models.state import GlobalState

try:
    from src.agents.builder import BuilderAgent
except ImportError:
    BuilderAgent = None # type: ignore


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

    def test_gate3_multiple_features(self, agent: BuilderAgent, state_with_idea: GlobalState) -> None:
        """
        Test that if multiple features are detected and none selected,
        the agent populates candidate_features and halts (returns state).
        """
        with patch.object(agent, "_extract_features", return_value=["Feature A long", "Feature B long", "Feature C long"]):
            result = agent.run(state_with_idea)

            assert "candidate_features" in result
            assert len(result["candidate_features"]) == 3
            assert result["candidate_features"] == ["Feature A long", "Feature B long", "Feature C long"]
            assert "mvp_spec" not in result or result["mvp_spec"] is None

    def test_gate3_single_selection(self, agent: BuilderAgent, state_with_idea: GlobalState) -> None:
        """
        Test that if a single feature is selected, generation proceeds.
        """
        state_with_idea.candidate_features = ["Feature A long desc", "Feature B long desc", "Feature C long desc"]
        state_with_idea.selected_feature = "Feature A long desc"

        # Mock V0Client
        with patch("src.agents.builder.V0Client") as mock_v0_cls:
            mock_v0 = mock_v0_cls.return_value
            mock_v0.generate_ui.return_value = "https://v0.dev/generated"

            # Mock MVP Spec creation
            with patch.object(agent, "_create_mvp_spec", return_value=MVPSpec(
                app_name="Test App",
                core_feature="Feature A long desc",
                components=["Comp1"]
            )):
                result = agent.run(state_with_idea)

                assert "mvp_spec" in result
                assert "mvp_url" in result
                assert result["mvp_url"] == "https://v0.dev/generated"
                assert result["mvp_spec"].core_feature == "Feature A long desc"

    def test_gate3_auto_select_single_feature(self, agent: BuilderAgent, state_with_idea: GlobalState) -> None:
        """
        Test that if only 1 feature is found in solution, it is auto-selected.
        """
        with patch.object(agent, "_extract_features", return_value=["Only Feature long enough"]):
            with patch("src.agents.builder.V0Client") as mock_v0_cls:
                mock_v0 = mock_v0_cls.return_value
                mock_v0.generate_ui.return_value = "https://v0.dev/auto"

                with patch.object(agent, "_create_mvp_spec", return_value=MVPSpec(
                    app_name="Test App",
                    core_feature="Only Feature long enough",
                    components=["Comp1"]
                )):
                    result = agent.run(state_with_idea)

                    assert result["selected_feature"] == "Only Feature long enough"
                    assert result["mvp_url"] == "https://v0.dev/auto"

    def test_extract_features_real_call(self, agent: BuilderAgent) -> None:
        """Test _extract_features with mocked LLM response to cover the method."""
        with patch("src.agents.builder.ChatPromptTemplate.from_messages") as mock_prompt:
             mock_prompt_tmpl = MagicMock()
             mock_prompt.return_value = mock_prompt_tmpl

             mock_model_runnable = MagicMock()
             agent.llm.with_structured_output.return_value = mock_model_runnable

             mock_chain = MagicMock()
             mock_prompt_tmpl.__or__.return_value = mock_chain
             mock_chain.invoke.return_value = FeatureList(features=["F1", "F2"])

             features = agent._extract_features("solution")
             assert features == ["F1", "F2"]

    def test_extract_features_failure(self, agent: BuilderAgent) -> None:
        """Test _extract_features failure handling."""
        with patch("src.agents.builder.ChatPromptTemplate.from_messages") as mock_prompt:
             # Ensure the chain invoke raises exception
             mock_chain = MagicMock()
             mock_prompt.return_value.__or__.return_value = mock_chain
             mock_chain.invoke.side_effect = Exception("LLM Fail")

             features = agent._extract_features("solution")
             assert features == []

    def test_create_mvp_spec_real_call(self, agent: BuilderAgent) -> None:
        """Test _create_mvp_spec with mocked LLM response."""
        with patch("src.agents.builder.ChatPromptTemplate.from_messages") as mock_prompt:
             mock_chain = MagicMock()
             mock_prompt.return_value.__or__.return_value = mock_chain

             expected_spec = MVPSpec(
                app_name="App", core_feature="Feature long enough", components=["Comp1"]
             )
             mock_chain.invoke.return_value = expected_spec

             spec = agent._create_mvp_spec("App", "Feature long enough", "Context")
             assert spec == expected_spec

    def test_create_mvp_spec_failure(self, agent: BuilderAgent) -> None:
        """Test _create_mvp_spec failure handling."""
        with patch("src.agents.builder.ChatPromptTemplate.from_messages") as mock_prompt:
             mock_chain = MagicMock()
             mock_prompt.return_value.__or__.return_value = mock_chain
             mock_chain.invoke.side_effect = Exception("Spec Fail")

             spec = agent._create_mvp_spec("App", "Feature long enough", "Context")
             # Fallback
             assert spec.app_name == "App"
             assert spec.core_feature == "Feature long enough"

    def test_no_idea_selected(self, agent: BuilderAgent) -> None:
        """Test run with no selected idea."""
        state = GlobalState(topic="Empty")
        result = agent.run(state)
        assert result == {}

    def test_no_features_extracted(self, agent: BuilderAgent, state_with_idea: GlobalState) -> None:
        """Test run when feature extraction fails."""
        with patch.object(agent, "_extract_features", return_value=[]):
            result = agent.run(state_with_idea)
            assert result == {}

    def test_generation_v0_exception(self, agent: BuilderAgent, state_with_idea: GlobalState) -> None:
        """Test handling of V0GenerationError during generation."""
        state_with_idea.selected_feature = "Feature A long"

        with patch.object(agent, "_create_mvp_spec", return_value=MVPSpec(
            app_name="App", core_feature="Feature A long", components=[]
        )), patch("src.agents.builder.V0Client") as mock_v0_cls:
            # Raise specific V0 exception
            mock_v0_cls.return_value.generate_ui.side_effect = V0GenerationError("API Failure")

            result = agent.run(state_with_idea)
            # Should return partial state
            assert "mvp_spec" in result
            assert "mvp_url" not in result
