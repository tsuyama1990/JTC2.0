from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr

from src.core.factory import AgentFactory

# Note: We patch 'src.core.llm.settings' instead of 'OPENAI_API_KEY'
from src.core.llm import get_llm
from src.domain_models.simulation import Role
from src.domain_models.state import GlobalState


@pytest.fixture
def mock_openai_key() -> SecretStr:
    return SecretStr("sk-12345678901234567890")


@pytest.fixture
def mock_tavily_key() -> SecretStr:
    return SecretStr("tvly-12345678901234567890")


import os


def test_config_values(mock_openai_key: SecretStr, mock_tavily_key: SecretStr) -> None:
    """Test that default settings are loaded correctly from environment variables."""
    from src.core.config import Settings

    with patch.dict(
        os.environ,
        {
            "OPENAI_API_KEY": mock_openai_key.get_secret_value(),
            "TAVILY_API_KEY": mock_tavily_key.get_secret_value(),
            "UI_PAGE_SIZE": "10",
            "SIMULATION_WIDTH": "256",
            "SIMULATION_HEIGHT": "256",
            "SIMULATION_FPS": "30",
            "SIMULATION_TITLE": "Test",
            "COLOR_BG": "0",
            "COLOR_TEXT": "7",
            "SIMULATION_CHARS_PER_LINE": "30",
            "SIMULATION_LINE_HEIGHT": "8",
            "SIMULATION_DIALOGUE_X": "4",
            "SIMULATION_DIALOGUE_Y": "180",
            "SIMULATION_MAX_Y": "240",
            "SIMULATION_WAITING_MSG": "Waiting...",
            "SIMULATION_TURN_SEQUENCE": '["NEW_EMPLOYEE", "FINANCE"]',
            "SIMULATION_CONSOLE_SLEEP": "1.0",
            "SIMULATION_MAX_TURNS": "3",
            "MIN_ROI_THRESHOLD": "1.5",
            "DEFAULT_CAC": "100.0",
            "DEFAULT_ARPU": "50.0",
            "DEFAULT_CHURN": "0.05",
            "RINGI_SHO_PATH": "outputs/RINGI_SHO.md",
            "GOV_SEARCH_QUERY_TEMPLATE": "test {industry}",
            "V0_API_URL": "https://test.v0.dev",
            "LLM_MODEL": "gpt-4o",
            "RAG_PERSIST_DIR": "test_dir",
            "RAG_ALLOWED_PATHS": '["test_dir"]',
            "SEARCH_QUERY_TEMPLATE": "test {topic}",
            "LOG_LEVEL": "INFO",
        },
        clear=True,
    ):
        s = Settings()
        assert s.llm_model == "gpt-4o"
        assert s.search_max_results == 5
        assert s.openai_api_key.get_secret_value() == mock_openai_key.get_secret_value()


@patch("src.core.llm.get_settings")
def test_get_llm_success(mock_get_settings: MagicMock, mock_openai_key: SecretStr) -> None:
    mock_settings = mock_get_settings.return_value
    mock_settings.openai_api_key = mock_openai_key
    mock_settings.llm_model = "gpt-4o"

    llm = get_llm()
    assert llm.model_name == "gpt-4o"
    assert llm.openai_api_key == mock_openai_key


@patch("src.core.llm.get_settings")
def test_get_llm_override(mock_get_settings: MagicMock, mock_openai_key: SecretStr) -> None:
    mock_settings = mock_get_settings.return_value
    mock_settings.openai_api_key = mock_openai_key

    llm = get_llm(model="gpt-3.5-turbo")
    assert llm.model_name == "gpt-3.5-turbo"


@patch("src.core.llm.get_settings")
def test_get_llm_missing_key(mock_get_settings: MagicMock) -> None:
    # Clear lru_cache to ensure we get a fresh execution
    get_llm.cache_clear()
    assert get_llm.cache_info().currsize == 0

    mock_settings = mock_get_settings.return_value
    mock_settings.openai_api_key = None

    with pytest.raises(ValueError, match="LLM configuration invalid"):
        get_llm()

    # Clear again for safety
    get_llm.cache_clear()


@patch("src.core.factory.get_llm")
def test_agent_factory_ideator_builder(mock_get_llm: MagicMock) -> None:
    mock_llm_instance = MagicMock()
    mock_get_llm.return_value = mock_llm_instance

    ideator = AgentFactory.get_ideator_agent()
    assert ideator is not None
    assert ideator.llm == mock_llm_instance

    builder = AgentFactory.get_builder_agent()
    assert builder is not None
    assert builder.llm == mock_llm_instance


def test_agent_factory_governance() -> None:
    governance = AgentFactory.get_governance_agent()
    assert governance is not None
    from src.agents.governance import GovernanceAgent

    assert isinstance(governance, GovernanceAgent)
    # Since governance doesn't inherit from BaseAgent or have a role, we just check instance and dependencies if any


@patch("src.core.factory.get_llm")
@patch("src.core.factory.get_settings")
def test_agent_factory_persona(
    mock_get_settings: MagicMock,
    mock_get_llm: MagicMock,
    mock_tavily_key: SecretStr,
    tmp_path: Path,
) -> None:
    mock_llm = MagicMock()
    mock_get_llm.return_value = mock_llm

    mock_settings = MagicMock()
    mock_settings.tavily_api_key.get_secret_value.return_value = mock_tavily_key.get_secret_value()

    test_path = tmp_path / "test_path"
    test_path.mkdir(exist_ok=True)
    test_path_str = str(test_path.resolve())

    mock_settings.rag_persist_dir = test_path_str
    mock_settings.rag_allowed_paths = [str(tmp_path.resolve())]
    mock_get_settings.return_value = mock_settings

    with patch("src.agents.cpo.RAG") as mock_rag:
        # CPO Agent without state
        cpo = AgentFactory.get_persona_agent(Role.CPO)
        assert cpo is not None
        assert cpo.llm == mock_llm

        # CPO Agent with state
        state = GlobalState()
        state.rag_index_path = test_path_str
        cpo_state = AgentFactory.get_persona_agent(Role.CPO, state)
        assert cpo_state is not None
        assert cpo_state.llm == mock_llm
        mock_rag.assert_called_with(persist_dir=test_path_str)

    # Other personas
    new_employee = AgentFactory.get_persona_agent(Role.NEW_EMPLOYEE)
    assert new_employee is not None
    assert new_employee.llm == mock_llm

    finance = AgentFactory.get_persona_agent(Role.FINANCE)
    assert finance is not None
    assert finance.llm == mock_llm

    sales = AgentFactory.get_persona_agent(Role.SALES)
    assert sales is not None
    assert sales.llm == mock_llm

    # Invalid role
    with pytest.raises(ValueError, match="Unknown role"):
        AgentFactory.get_persona_agent("INVALID_ROLE")  # type: ignore[arg-type]
