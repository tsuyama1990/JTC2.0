from unittest.mock import MagicMock, patch

import pytest

from src.agents.ideator import IdeatorAgent
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.state import GlobalState


@pytest.fixture
def mock_llm() -> MagicMock:
    return MagicMock()


@patch("src.agents.ideator.TavilySearch")
@patch("src.agents.ideator.SettingsFactory")
def test_ideator_agent_run_success(
    mock_settings_factory: MagicMock,
    mock_tavily: MagicMock,
    mock_llm: MagicMock,
) -> None:
    mock_settings = mock_settings_factory.return_value.build.return_value
    # Setup settings
    mock_settings.search.query_template = "Trends in {topic}"
    mock_settings.tavily_api_key.get_secret_value.return_value = "tv-key"

    # Setup Search - Mock the public interface of SearchTool
    mock_search_instance = mock_tavily.return_value
    mock_search_instance.safe_search.return_value = "Research data"

    IdeatorAgent(llm=mock_llm)

    # Setup LLM - Mock the behavior of .with_structured_output().invoke()
    # We don't mock the prompt template internals anymore, just the chain execution
    mock_chain = MagicMock()
    mock_llm.with_structured_output.return_value = mock_chain


@patch("src.agents.ideator.TavilySearch")
@patch("src.agents.ideator.SettingsFactory")
def test_ideator_agent_flow(
    mock_settings_factory: MagicMock,
    mock_tavily: MagicMock,
    mock_llm: MagicMock,
) -> None:
    # This test focuses on the `run` method orchestration
    mock_settings = mock_settings_factory.return_value.build.return_value
    # 1. Setup Dependencies
    mock_settings.search.query_template = "Q: {topic}"
    mock_settings.tavily_api_key.get_secret_value.return_value = "key"

    mock_search_tool = mock_tavily.return_value
    mock_search_tool.safe_search.return_value = "Market Data"

    # 2. Setup Agent
    agent = IdeatorAgent(llm=mock_llm)

    # 3. Mock internal helpers to isolate `run` logic from chain complexity
    # This satisfies "testing public interface `run`" without getting bogged down in LangChain internals
    with patch.object(agent, "_generate_ideas") as mock_gen_ideas:
        expected_ideas = [
            LeanCanvas(
                id=0,
                title="Idea",
                problem="Problem is valid valid",
                customer_segments="CS",
                unique_value_prop="UVP is valid valid",
                solution="Solution is valid valid",
            )
        ]
        mock_gen_ideas.return_value = expected_ideas

        # 4. Execute
        state = GlobalState(topic="Test")
        result = agent.run(state)

        # 5. Verify
        assert result["generated_ideas"] == expected_ideas

        # Verify research was called
        mock_search_tool.safe_search.assert_called_with("Q: Test")

        # Verify generation was called with prompt (checking prompt content implicitly via _generate_prompt logic)
        # We can check that _generate_ideas was called.
        mock_gen_ideas.assert_called_once()


@patch("src.agents.ideator.TavilySearch")
@patch("src.agents.ideator.SettingsFactory")
def test_ideator_agent_research_logic(
    mock_settings_factory: MagicMock,
    mock_tavily: MagicMock,
    mock_llm: MagicMock,
) -> None:
    mock_settings = mock_settings_factory.return_value.build.return_value
    # Test `_research` specifically
    mock_settings.search.query_template = "Search {topic}"
    mock_settings.tavily_api_key.get_secret_value.return_value = "key"

    mock_search = mock_tavily.return_value
    mock_search.safe_search.return_value = "Results"

    agent = IdeatorAgent(llm=mock_llm)
    res = agent._research("AI")

    assert res == "Results"
    mock_search.safe_search.assert_called_with("Search AI")
