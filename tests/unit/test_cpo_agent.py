from unittest.mock import MagicMock, patch

from src.agents.personas import CPOAgent
from src.domain_models.simulation import Role


@patch("src.agents.personas.ChatOpenAI")
def test_cpo_agent_init(mock_llm: MagicMock) -> None:
    agent = CPOAgent(llm=mock_llm)
    assert agent.role == Role.CPO
    assert "Chief Product Officer" in agent.system_prompt
    assert "do not speak in the main meeting" in agent.system_prompt

@patch("src.agents.personas.ChatOpenAI")
def test_cpo_research(mock_llm: MagicMock) -> None:
    agent = CPOAgent(llm=mock_llm)
    agent.search_tool = MagicMock()
    agent.search_tool.safe_search.return_value = "Found case study"

    result = agent._research("SaaS Platform")
    assert result == "Found case study"
    agent.search_tool.safe_search.assert_called_with("successful business models and case studies similar to SaaS Platform")
