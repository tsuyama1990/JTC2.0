from unittest.mock import MagicMock, patch

from src.core.nodes import alternative_analysis_node, persona_node, vpc_node
from src.domain_models.state import GlobalState


@patch("src.core.nodes.AgentFactory")
def test_persona_node(mock_agent_factory: MagicMock) -> None:
    mock_agent = MagicMock()
    mock_agent.run.return_value = {"target_persona": "mock_persona"}
    mock_agent_factory.get_persona_generator_agent.return_value = mock_agent

    state = GlobalState()
    result = persona_node(state)

    assert result == {"target_persona": "mock_persona"}
    mock_agent_factory.get_persona_generator_agent.assert_called_once()
    mock_agent.run.assert_called_once_with(state)


@patch("src.core.nodes.AgentFactory")
def test_alternative_analysis_node(mock_agent_factory: MagicMock) -> None:
    mock_agent = MagicMock()
    mock_agent.run.return_value = {"alternative_analysis": "mock_analysis"}
    mock_agent_factory.get_alternative_analysis_agent.return_value = mock_agent

    state = GlobalState()
    result = alternative_analysis_node(state)

    assert result == {"alternative_analysis": "mock_analysis"}
    mock_agent_factory.get_alternative_analysis_agent.assert_called_once()
    mock_agent.run.assert_called_once_with(state)


@patch("src.core.nodes.AgentFactory")
def test_vpc_node(mock_agent_factory: MagicMock) -> None:
    mock_agent = MagicMock()
    mock_agent.run.return_value = {"value_proposition_canvas": "mock_vpc"}
    mock_agent_factory.get_vpc_agent.return_value = mock_agent

    state = GlobalState()
    result = vpc_node(state)

    assert result == {"value_proposition_canvas": "mock_vpc"}
    mock_agent_factory.get_vpc_agent.assert_called_once()
    mock_agent.run.assert_called_once_with(state)
