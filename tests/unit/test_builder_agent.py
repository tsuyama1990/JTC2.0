from typing import cast
from unittest.mock import MagicMock

import pytest

from src.agents.builder import FeatureList
from src.domain_models.lean_canvas import LeanCanvas
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
        mock_model_runnable = MagicMock()
        mock_llm = cast(MagicMock, agent.llm)
        mock_llm.with_structured_output.return_value = mock_model_runnable

        # Mock the invoke result
        mock_model_runnable.invoke.return_value = FeatureList(features=["F1", "F2"])

        # Execute with input long enough to pass short-check
        input_text = "solution that is sufficiently long to pass the length validation check"
        features = list(agent._extract_features(input_text))

        assert features == ["F1", "F2"]
        # Verify invocation happened
        mock_model_runnable.invoke.assert_called()
