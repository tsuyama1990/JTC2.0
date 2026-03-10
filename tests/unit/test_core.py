from unittest.mock import MagicMock, patch
import pytest
from pydantic import SecretStr

from src.core.llm import LLMFactory, LLMProvider
from src.core.factory import AgentFactory
from src.domain_models.simulation import Role

def test_config_values() -> None:
    from src.core.config import Settings
    s = Settings(
        OPENAI_API_KEY="sk-12345678901234567890",
        TAVILY_API_KEY="tvly-12345678901234567890",
    )
    assert s.llm_model == "gpt-4o"
    assert s.search.max_results == 5
    assert s.openai_api_key.get_secret_value() == "sk-12345678901234567890"

@patch("src.core.validators.ApiKeyValidator.validate_openai")
def test_get_llm_success(mock_validate: MagicMock) -> None:
    mock_settings = MagicMock()
    mock_settings.openai_api_key = SecretStr("test-key")
    mock_settings.llm_model = "gpt-4o"

    llm_factory = LLMFactory(LLMProvider(mock_settings))
    llm = llm_factory.get_llm()
    assert llm.model_name == "gpt-4o"
    assert llm.openai_api_key.get_secret_value() == "test-key"
    mock_validate.assert_called_once()

@patch("src.core.validators.ApiKeyValidator.validate_openai")
def test_get_llm_override(mock_validate: MagicMock) -> None:
    mock_settings = MagicMock()
    mock_settings.openai_api_key = SecretStr("test-key")

    llm_factory = LLMFactory(LLMProvider(mock_settings))
    llm = llm_factory.get_llm(model="gpt-3.5-turbo")
    assert llm.model_name == "gpt-3.5-turbo"

@patch("src.core.validators.ApiKeyValidator.validate_openai")
def test_get_llm_missing_key(mock_validate: MagicMock) -> None:
    mock_settings = MagicMock()
    mock_settings.openai_api_key = None

    with pytest.raises(ValueError, match="LLM configuration invalid"):
        llm_factory = LLMFactory(LLMProvider(mock_settings))
        llm_factory.get_llm()

@patch("src.agents.governance.FileService")
def test_agent_factory_methods(mock_fs):
    mock_llm = MagicMock()
    mock_settings = MagicMock()
    factory = AgentFactory(mock_llm, mock_settings)

    assert factory.get_ideator_agent() is not None
    assert factory.get_builder_agent() is not None
    assert factory.get_governance_agent() is not None
    assert factory.get_remastered_agent() is not None
    assert factory.get_output_generation_agent() is not None
    assert factory.get_virtual_customer_agent() is not None
    assert factory.get_hacker_agent() is not None
    assert factory.get_hipster_agent() is not None
    assert factory.get_hustler_agent() is not None

@patch("src.agents.cpo.RAG")
def test_agent_factory_persona_agents(mock_rag):
    mock_llm = MagicMock()
    mock_settings = MagicMock()
    factory = AgentFactory(mock_llm, mock_settings)

    mock_state = MagicMock()
    mock_state.rag_index_path = "path/to/rag"

    assert factory.get_persona_agent(Role.CPO, state=mock_state) is not None
    assert factory.get_persona_agent(Role.NEW_EMPLOYEE) is not None
    assert factory.get_persona_agent(Role.FINANCE) is not None
    assert factory.get_persona_agent(Role.SALES) is not None

    with pytest.raises(ValueError, match="Unknown role requested"):
        factory.get_persona_agent("UNKNOWN_ROLE")
