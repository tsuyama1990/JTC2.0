from unittest.mock import MagicMock, patch

from src.agents.cpo import CPOAgent
from src.domain_models.simulation import Role


@patch("src.agents.cpo.RAG")
@patch("src.agents.cpo.ChatOpenAI")
def test_cpo_agent_init(mock_llm: MagicMock, mock_rag: MagicMock) -> None:
    agent = CPOAgent(llm=mock_llm)
    assert agent.role == Role.CPO
    assert "Chief Product Officer" in agent.system_prompt
    assert "do not speak in the main meeting" in agent.system_prompt

@patch("src.agents.cpo.RAG")
@patch("src.agents.cpo.ChatOpenAI")
def test_cpo_research(mock_llm: MagicMock, mock_rag: MagicMock) -> None:
    agent = CPOAgent(llm=mock_llm)
    # Mock RAG inside agent
    agent.rag = MagicMock()
    agent.rag.query.return_value = "Found customer data"

    result = agent._research_impl("SaaS Platform")
    assert result == "Found customer data"
    agent.rag.query.assert_called()
