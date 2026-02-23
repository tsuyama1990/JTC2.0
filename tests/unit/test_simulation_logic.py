from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from src.agents.personas import FinanceAgent, NewEmployeeAgent
from src.core.simulation import create_simulation_graph
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.metrics import AARRR
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

    res = agent._research_impl("AI")

    assert res == "Risks found."
    mock_search.safe_search.assert_called_with("market risks and costs for AI")


def test_cached_research_logic(mock_llm: MagicMock) -> None:
    """Test caching and rate limiting logic."""
    mock_search = MagicMock()
    mock_search.safe_search.side_effect = ["Result 1", "Result 2"]

    agent = FinanceAgent(llm=mock_llm, search_tool=mock_search)
    agent._min_request_interval = 0.01 # Minimal delay for test speed but > 0 to test logic path

    # First call
    res1 = agent._cached_research("Topic A")
    assert res1 == "Result 1"

    # Second call (Should hit cache)
    res2 = agent._cached_research("Topic A")
    assert res2 == "Result 1"

    assert mock_search.safe_search.call_count == 1

    # Different topic (Should call backend)
    res3 = agent._cached_research("Topic B")
    assert res3 == "Result 2"
    assert mock_search.safe_search.call_count == 2


def test_rate_limit_wait(mock_llm: MagicMock) -> None:
    """Verify rate limiting wait behavior."""
    import time
    mock_search = MagicMock()
    agent = FinanceAgent(llm=mock_llm, search_tool=mock_search)
    agent._min_request_interval = 0.1

    start = time.time()
    agent._rate_limit_wait()
    # First call sets time, no wait if first? logic: if elapsed < min -> sleep.
    # Init last_request_time is 0.0. Time.time() is huge. elapsed is huge. No sleep.

    # Manually set last request time to now
    agent._last_request_time = time.time()
    agent._rate_limit_wait()
    end = time.time()

    assert (end - start) >= 0.1


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

    with patch.object(agent, "_generate_response", return_value="Defended!"):
         result = agent.run(mock_state)

         assert "debate_history" in result
         assert len(result["debate_history"]) == 1
         assert result["debate_history"][0].content == "Defended!"
         assert result["debate_history"][0].role == Role.NEW_EMPLOYEE


def test_metrics_boundary_conditions() -> None:
    """Test boundary conditions for numeric fields in Metrics (AARRR)."""
    # Valid low boundary (0.0)
    metrics = AARRR(acquisition=0.0)
    assert metrics.acquisition == 0.0

    # Invalid low boundary (-0.1)
    with pytest.raises(ValidationError) as exc:
        AARRR(acquisition=-0.1)
    assert any(e["loc"] == ("acquisition",) for e in exc.value.errors())

    # Valid high boundary for retention (100.0)
    metrics_ret = AARRR(retention=100.0)
    assert metrics_ret.retention == 100.0

    # Invalid high boundary for retention (100.1)
    with pytest.raises(ValidationError) as exc:
        AARRR(retention=100.1)
    assert any(e["loc"] == ("retention",) for e in exc.value.errors())
