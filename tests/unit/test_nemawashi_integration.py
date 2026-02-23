from unittest.mock import MagicMock, patch

from src.agents.cpo import CPOAgent
from src.domain_models.simulation import AgentState, Role
from src.domain_models.state import GlobalState
from tests.conftest import DUMMY_ENV_VARS


@patch.dict("os.environ", DUMMY_ENV_VARS)
@patch("src.agents.cpo.NemawashiEngine")
def test_cpo_uses_nemawashi(mock_engine_cls):
    # Setup
    mock_engine = mock_engine_cls.return_value
    mock_engine.calculate_consensus.return_value = [0.6, 0.4]
    mock_engine.identify_influencers.return_value = ["Finance Manager"]

    llm = MagicMock()
    # Mock LLM response
    llm.invoke.return_value.content = "Advice"

    # We mock RAG to avoid filesystem access
    with patch("src.agents.cpo.RAG"):
        agent = CPOAgent(llm)

        # State with agents
        state = GlobalState()
        # We need to populate agent_states to have a valid network
        state.agent_states = {
            Role.NEW_EMPLOYEE: AgentState(role=Role.NEW_EMPLOYEE),
            Role.FINANCE: AgentState(role=Role.FINANCE)
        }

        # Run
        agent.run(state)

        # Verify
        mock_engine.calculate_consensus.assert_called_once()
        mock_engine.identify_influencers.assert_called_once()
