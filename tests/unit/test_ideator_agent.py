from unittest.mock import MagicMock, patch

import pytest

from src.agents.ideator import IdeatorAgent, LeanCanvasList
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.state import GlobalState


@pytest.fixture
def mock_llm() -> MagicMock:
    return MagicMock()


@patch("src.agents.ideator.ChatPromptTemplate")
@patch("src.agents.ideator.TavilySearch")
def test_ideator_agent_run_success(
    mock_tavily: MagicMock, mock_prompt_cls: MagicMock, mock_llm: MagicMock
) -> None:
    # Setup
    mock_search_instance = mock_tavily.return_value
    mock_search_instance.search.return_value = "Research data"

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
            problem="P",
            customer_segments="C",
            unique_value_prop="UVP",
            solution="S",
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
    mock_search_instance.search.assert_called_with(
        "emerging business trends and painful problems in Test Topic"
    )


@patch("src.agents.ideator.ChatPromptTemplate")
@patch("src.agents.ideator.TavilySearch")
def test_ideator_agent_fail(
    mock_tavily: MagicMock, mock_prompt_cls: MagicMock, mock_llm: MagicMock
) -> None:
    # Setup
    mock_search_instance = mock_tavily.return_value
    mock_search_instance.search.return_value = "Research data"

    agent = IdeatorAgent(llm=mock_llm)

    # Mock chain construction
    mock_prompt = mock_prompt_cls.from_messages.return_value
    mock_chain = MagicMock()
    mock_prompt.__or__.return_value = mock_chain

    # Mock invoke result
    mock_chain.invoke.return_value = None

    # Execution
    state = GlobalState(topic="Test Topic")
    result = agent.run(state)

    # Verification
    assert result["generated_ideas"] == []
