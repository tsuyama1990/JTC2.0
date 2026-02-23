from unittest.mock import MagicMock, patch

import pytest

from src.agents.personas import FinanceAgent, NewEmployeeAgent
from src.core.simulation import create_simulation_graph
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.simulation import Role
from src.domain_models.state import GlobalState


@pytest.fixture
def mock_llm() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_state() -> GlobalState:
    """Create a mock GlobalState for simulation."""
    return GlobalState(
        topic="AI Pet Sitter",
        selected_idea=LeanCanvas(
            id=0,
            title="AI Pet Sitter",
            problem="Pets get lonely.",
            solution="AI robot entertains pets.",
            customer_segments="Pet owners",
            unique_value_prop="24/7 pet care",
        ),
        debate_history=[],
        simulation_active=True,
    )


def test_simulation_flow_initialization(mock_state: GlobalState) -> None:
    """Test that simulation starts correctly."""
    assert mock_state.simulation_active is True
    assert len(mock_state.debate_history) == 0


def test_finance_agent_research_logic(mock_llm: MagicMock) -> None:
    """Test FinanceAgent research logic."""
    mock_search = MagicMock()
    mock_search.safe_search.return_value = "Risks found."

    agent = FinanceAgent(llm=mock_llm, search_tool=mock_search)
    res = agent._research("AI")

    assert res == "Risks found."
    mock_search.safe_search.assert_called_with("market risks and costs for AI")


@patch("src.agents.personas.TavilySearch")
@patch("src.core.simulation.get_llm")
def test_simulation_graph_structure(mock_get_llm: MagicMock, mock_tavily: MagicMock) -> None:
    """Test the structure of the simulation graph."""
    mock_get_llm.return_value = MagicMock()
    mock_tavily.return_value = MagicMock()

    graph = create_simulation_graph()
    assert graph is not None


@patch("src.agents.personas.TavilySearch")
def test_persona_agent_run(mock_tavily: MagicMock, mock_llm: MagicMock, mock_state: GlobalState) -> None:
    """Test PersonaAgent.run logic."""
    mock_tavily.return_value = MagicMock()

    agent = NewEmployeeAgent(llm=mock_llm)

    # Mock _generate_response to isolate run logic
    with patch.object(agent, "_generate_response", return_value="Defended!"):
         result = agent.run(mock_state)

         assert "debate_history" in result
         # Initial history was empty, so result has 1 item
         assert len(result["debate_history"]) == 1
         assert result["debate_history"][0].content == "Defended!"
         assert result["debate_history"][0].role == Role.NEW_EMPLOYEE
