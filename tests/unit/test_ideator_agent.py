from unittest.mock import MagicMock, patch

import pytest

from src.agents.ideator import IdeatorAgent, LeanCanvasList
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.state import GlobalState


@pytest.fixture
def mock_llm() -> MagicMock:
    return MagicMock()


@patch("src.agents.ideator.settings")
@patch("src.agents.ideator.ChatPromptTemplate")
@patch("src.agents.ideator.TavilySearch")
def test_ideator_agent_run_success(
    mock_tavily: MagicMock,
    mock_prompt_cls: MagicMock,
    mock_settings: MagicMock,
    mock_llm: MagicMock
) -> None:
    # Setup settings
    mock_settings.search_query_template = "Trends in {topic}"

    # Setup Search
    mock_search_instance = mock_tavily.return_value
    mock_search_instance.safe_search.return_value = "Research data"

    agent = IdeatorAgent(llm=mock_llm)

    # Mock chain construction
    mock_prompt = mock_prompt_cls.from_messages.return_value
    mock_chain = MagicMock()
    # prompt | llm_output -> chain
    mock_prompt.__or__.return_value = mock_chain

    # Mock invoke result
    canvases = [
        LeanCanvas(
            id=i,
            title=f"Idea {i}",
            problem="Problem statement here",
            customer_segments="Customer Segments",
            unique_value_prop="Unique Value Proposition",
            solution="Solution description here",
        )
        for i in range(10)
    ]
    mock_chain.invoke.return_value = LeanCanvasList(canvases=canvases)

    # Execution
    state = GlobalState(topic="Test Topic")
    result = agent.run(state)

    # Verification
    assert "generated_ideas" in result
    assert len(result["generated_ideas"]) == 10
    mock_search_instance.safe_search.assert_called_with("Trends in Test Topic")


@patch("src.agents.ideator.settings")
@patch("src.agents.ideator.ChatPromptTemplate")
@patch("src.agents.ideator.TavilySearch")
def test_ideator_agent_fail(
    mock_tavily: MagicMock,
    mock_prompt_cls: MagicMock,
    mock_settings: MagicMock,
    mock_llm: MagicMock
) -> None:
    # Setup settings
    mock_settings.search_query_template = "Trends in {topic}"

    # Setup Search
    mock_search_instance = mock_tavily.return_value
    mock_search_instance.safe_search.return_value = "Research data"

    agent = IdeatorAgent(llm=mock_llm)

    # Mock chain construction
    mock_prompt = mock_prompt_cls.from_messages.return_value
    mock_chain = MagicMock()
    mock_prompt.__or__.return_value = mock_chain

    # Mock invoke result - Simulate generic Exception from LLM
    mock_chain.invoke.side_effect = Exception("LLM Error")

    # Execution
    state = GlobalState(topic="Test Topic")
    result = agent.run(state)

    # Verification - Should return empty list gracefully
    assert result["generated_ideas"] == []
