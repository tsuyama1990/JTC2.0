import os
from unittest.mock import MagicMock, patch

import pytest

from src.core.config import get_settings
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.state import GlobalState
from src.domain_models.mvp import MVPSpec
from tests.conftest import DUMMY_ENV_VARS

# We assume integration via graph, but for UAT we can simulate the node execution
# since we don't have the full graph running in main.py yet.
# However, we should test the graph node integration if possible.

try:
    from src.agents.builder import BuilderAgent
except ImportError:
    BuilderAgent = None

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
        # It should detect multiple features and return candidates
        mock_llm = MagicMock()
        agent = BuilderAgent(llm=mock_llm)

        with patch.object(agent, "_extract_features", return_value=["Feature 1 desc", "Feature 2 desc", "Feature 3 desc"]):
            result = agent.run(initial_state)

            assert "candidate_features" in result
            assert len(result["candidate_features"]) == 3
            assert "mvp_url" not in result # Should NOT generate yet

    def test_uat_c05_02_mvp_generation(self, initial_state: GlobalState) -> None:
        """
        Scenario 2: MVP Generation
        Verify v0.dev call after selection.
        """
        if BuilderAgent is None:
            pytest.skip("BuilderAgent not implemented")

        get_settings.cache_clear()

        # Setup state with selection
        initial_state.candidate_features = ["Feature 1 desc", "Feature 2 desc", "Feature 3 desc"]
        initial_state.selected_feature = "Feature 2 desc"

        mock_llm = MagicMock()
        agent = BuilderAgent(llm=mock_llm)

        # Mock V0
        with patch("src.agents.builder.V0Client") as mock_v0_cls:
            mock_v0 = mock_v0_cls.return_value
            mock_v0.generate_ui.return_value = "https://v0.dev/uat-result"

            # Mock Spec Creation
            with patch.object(agent, "_create_mvp_spec", return_value=MVPSpec(
                app_name="UAT App",
                core_feature="Feature 2 desc",
                components=["Hero"]
            )):
                result = agent.run(initial_state)

                assert result["mvp_url"] == "https://v0.dev/uat-result"
                assert result["mvp_spec"].core_feature == "Feature 2 desc"
