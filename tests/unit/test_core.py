from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr

# Note: We patch 'src.core.llm.settings' instead of 'OPENAI_API_KEY'
from src.core.llm import get_llm


def test_config_values() -> None:
    """Test that default settings are loaded correctly."""
    from src.core.config import Settings

    # Use environment variable naming for Pydantic BaseSettings init
    s = Settings(
        OPENAI_API_KEY=SecretStr("sk-12345678901234567890"),
        TAVILY_API_KEY=SecretStr("tvly-12345678901234567890"),
    )
    assert s.llm_model == "gpt-4o"
    assert s.search_max_results == 5
    assert s.openai_api_key == SecretStr("sk-12345678901234567890")


@patch("src.core.llm.get_settings")
def test_get_llm_success(mock_get_settings: MagicMock) -> None:
    mock_settings = mock_get_settings.return_value
    mock_settings.openai_api_key = SecretStr("test-key")
    mock_settings.llm_model = "gpt-4o"

    llm = get_llm()
    assert llm.model_name == "gpt-4o"
    assert llm.openai_api_key == SecretStr("test-key")


@patch("src.core.llm.get_settings")
def test_get_llm_override(mock_get_settings: MagicMock) -> None:
    mock_settings = mock_get_settings.return_value
    mock_settings.openai_api_key = SecretStr("test-key")

    llm = get_llm(model="gpt-3.5-turbo")
    assert llm.model_name == "gpt-3.5-turbo"


@patch("src.core.llm.get_settings")
def test_get_llm_missing_key(mock_get_settings: MagicMock) -> None:
    # Clear lru_cache to ensure we get a fresh execution
    get_llm.cache_clear()

    mock_settings = mock_get_settings.return_value
    mock_settings.openai_api_key = None
    # Updated error message constant in Cycle 06
    with pytest.raises(ValueError, match="LLM configuration invalid"):
        get_llm()

    # Clear again for safety
    get_llm.cache_clear()


from unittest.mock import MagicMock, patch

from src.core.factory import AgentFactory
from src.domain_models.simulation import Role
from src.domain_models.state import GlobalState


@patch("src.core.factory.get_llm")
def test_agent_factory_ideator_builder(mock_get_llm: MagicMock) -> None:
    mock_get_llm.return_value = MagicMock()
    ideator = AgentFactory.get_ideator_agent()
    assert ideator is not None
    builder = AgentFactory.get_builder_agent()
    assert builder is not None


def test_agent_factory_governance() -> None:
    governance = AgentFactory.get_governance_agent()
    assert governance is not None


@patch("src.core.factory.get_llm")
@patch("src.core.factory.get_settings")
def test_agent_factory_persona(mock_get_settings: MagicMock, mock_get_llm: MagicMock) -> None:
    mock_llm = MagicMock()
    mock_get_llm.return_value = mock_llm

    mock_settings = MagicMock()
    mock_settings.tavily_api_key.get_secret_value.return_value = "tvly-test"
    from pathlib import Path

    test_path = str((Path.cwd() / "test_path").resolve())
    mock_settings.rag_persist_dir = test_path
    mock_settings.rag_allowed_paths = [str(Path.cwd().resolve())]
    mock_get_settings.return_value = mock_settings

    with patch("src.agents.cpo.RAG"):
        # CPO Agent without state
        cpo = AgentFactory.get_persona_agent(Role.CPO)
        assert cpo is not None

        # CPO Agent with state
        state = GlobalState()
        state.rag_index_path = test_path
        cpo_state = AgentFactory.get_persona_agent(Role.CPO, state)
        assert cpo_state is not None

    # Other personas
    new_employee = AgentFactory.get_persona_agent(Role.NEW_EMPLOYEE)
    assert new_employee is not None

    finance = AgentFactory.get_persona_agent(Role.FINANCE)
    assert finance is not None

    sales = AgentFactory.get_persona_agent(Role.SALES)
    assert sales is not None

    # Invalid role
    with pytest.raises(ValueError, match="Unknown role"):
        # We need an invalid enum member or string, but type system complains if we use a string.
        # We can mock it or use an undefined role string
        AgentFactory.get_persona_agent("INVALID_ROLE")  # type: ignore
