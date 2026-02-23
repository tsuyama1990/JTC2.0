from unittest.mock import MagicMock, patch

import pytest

from src.core.graph import solution_node
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.mvp import MVP, MVPSpec
from src.domain_models.state import GlobalState, Phase


class TestSolutionNode:
    @pytest.fixture
    def state(self) -> GlobalState:
        return GlobalState(
            phase=Phase.IDEATION, # Initial phase before node
            topic="Test",
            selected_idea=LeanCanvas(
                id=1,
                title="Test",
                problem="Problem is big enough.",
                solution="Solution with features.",
                customer_segments="Seg",
                unique_value_prop="Unique Value Proposition is long enough."
            ),
            # Mock target_persona to satisfy validation if needed
            # But currently verification validation requires it. Solution validation requires MVP.
            # But we are entering solution node, which creates MVP.
            # StateValidator checks requirements for the CURRENT phase in state.
            # If state.phase is IDEATION, validation passes.
            # solution_node updates phase to SOLUTION at the end.
        )

    def test_solution_node_success(self, state: GlobalState) -> None:
        """Test successful execution of solution_node."""
        # We need target_persona because solution_node checks it
        state.target_persona = MagicMock()

        with patch("src.core.graph.AgentFactory.get_builder_agent") as mock_factory:
            mock_agent = MagicMock()
            mock_factory.return_value = mock_agent

            # Builder returns updates
            mock_agent.run.return_value = {
                "mvp_spec": MVPSpec(app_name="App", core_feature="Feature long enough", components=[]),
                "mvp_url": "https://v0.dev/test"
            }

            result = solution_node(state)

            assert result["phase"] == Phase.SOLUTION
            assert "mvp_spec" in result
            assert "mvp_definition" in result
            assert isinstance(result["mvp_definition"], MVP)
            # Check URL match (stripping potential trailing slash normalization)
            assert str(result["mvp_definition"].v0_url).rstrip('/') == "https://v0.dev/test"

    def test_solution_node_gate3_interrupt(self, state: GlobalState) -> None:
        """Test interruption at Gate 3 (multiple features)."""
        state.target_persona = MagicMock()

        with patch("src.core.graph.AgentFactory.get_builder_agent") as mock_factory:
            mock_agent = MagicMock()
            mock_factory.return_value = mock_agent

            # Builder returns candidates, no spec
            mock_agent.run.return_value = {
                "candidate_features": ["F1", "F2"]
            }

            result = solution_node(state)

            assert result["phase"] == Phase.SOLUTION
            assert "candidate_features" in result
            assert "mvp_definition" not in result # Not created yet

            # Since mvp_definition is missing, if we run validation on NEW state (phase=SOLUTION), it will fail.
            # But solution_node returns dict. GlobalState update happens outside.
            # If the graph engine updates state and then validates...
            # The current implementation of validation is explicitly called at start of nodes.
            # So next node (pmf_node) will call validation.
            # And pmf_node expects mvp_definition.
            # If interrupt happens, user must provide input.
            # Then we resume?
            # If we resume, we re-run solution_node?
            # Or we continue to next node?
            # If we continue to pmf_node, it will fail validation if mvp_definition is missing.
            # So user must ensure MVP is defined or we loop back to solution_node?
            # This is complex LangGraph flow.
            # But for this unit test, we just check output of the function.
