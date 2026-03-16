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
            "MIN_TITLE_LENGTH": "3",
            "MAX_TITLE_LENGTH": "100",
            "MIN_CONTENT_LENGTH": "3",
            "MAX_CONTENT_LENGTH": "1000",
            "MIN_LIST_LENGTH": "1",
            "MAX_LIST_LENGTH": "20",
            "MAX_CUSTOM_METRICS": "50",
            "MIN_METRIC_VALUE": "0.0",
            "MAX_PERCENTAGE_VALUE": "100.0",
            "UI_MAX_MESSAGES": "100",
            "NEMAWASHI_MAX_STAKEHOLDERS": "50",
            "NEMAWASHI_MAX_STEPS": "50",
            "NEMAWASHI_TOLERANCE": "1e-4",
            "NEMAWASHI_NOMIKAI_BOOST": "0.2",
            "NEMAWASHI_NOMIKAI_REDUCTION": "0.1",
            "FILE_MAX_WORKERS": "5",
            "OUTPUT_DIR": "outputs",
            "GRAPH_INTERRUPT_POINTS": '["ideator", "verification", "solution_proposal", "pmf"]',
            "V0_RETRY_MAX": "3",
            "V0_API_KEY": "v0-12345678901234567890",
            "V0_RETRY_BACKOFF": "2.0",
            "COLOR_NEW_EMP": "8",
            "COLOR_FINANCE": "9",
            "COLOR_SALES": "10",
            "COLOR_CPO": "11",
            "MAX_LLM_RESPONSE_SIZE": "10000",
            "MAX_CONTENT_MULTIPLIER": "5",
            "MAX_SEARCH_RESULT_SIZE": "5000",
            "RAG_CHUNK_SIZE": "1024",
            "RAG_MAX_DOC_LENGTH": "1000000",
            "RAG_MAX_QUERY_LENGTH": "1000",
            "RAG_MAX_INDEX_SIZE_MB": "500",
            "RAG_RATE_LIMIT_INTERVAL": "0.1",
            "RAG_SCAN_DEPTH_LIMIT": "10",
            "RAG_BATCH_SIZE": "100",
            "RAG_QUERY_TIMEOUT": "30.0",
            "FEATURE_CHUNK_SIZE": "5",
            "CB_FAIL_MAX": "3",
            "CB_RESET_TIMEOUT": "300",
            "ITERATOR_SAFETY_LIMIT": "1000",
            "SEARCH_MAX_RESULTS": "5",
            "SEARCH_DEPTH": "advanced",
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
