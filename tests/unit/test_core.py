from src.core.config import Settings
from unittest.mock import patch
from unittest.mock import MagicMock

import pytest
from pydantic import SecretStr

# Note: We patch 'src.core.llm.settings' instead of 'OPENAI_API_KEY'
from src.core.llm import LLMFactory


def test_config_values() -> None:
    """Test that default settings are loaded correctly."""
    from src.core.config import Settings

    # Use environment variable naming for Pydantic BaseSettings init
    s = Settings(
        OPENAI_API_KEY=SecretStr("sk-12345678901234567890"),
        TAVILY_API_KEY=SecretStr("tvly-12345678901234567890"),
    )
    assert s.llm_model == "gpt-4o"
    assert s.search.max_results == 5
    assert s.openai_api_key == SecretStr("sk-12345678901234567890")


@patch("src.core.validators.ApiKeyValidator.validate_openai")
def test_get_llm_success(mock_validate: MagicMock) -> None:
    from src.core.config import Settings
    from src.core.llm import LLMProvider
    mock_settings = Settings(OPENAI_API_KEY=SecretStr("test-key" * 10), TAVILY_API_KEY=SecretStr("dummy" * 10))
    mock_settings.llm_model = "gpt-4o"

    provider = LLMProvider(settings=mock_settings)
    llm_factory = LLMFactory(provider=provider)
    llm = llm_factory.get_llm()
    assert llm.model_name == "gpt-4o"
    mock_validate.assert_called_once()


@patch("src.core.validators.ApiKeyValidator.validate_openai")
def test_get_llm_override(mock_validate: MagicMock) -> None:
    from src.core.config import Settings
    from src.core.llm import LLMProvider
    mock_settings = Settings(OPENAI_API_KEY=SecretStr("test-key" * 10), TAVILY_API_KEY=SecretStr("dummy" * 10))

    provider = LLMProvider(settings=mock_settings)
    llm_factory = LLMFactory(provider=provider)
    llm = llm_factory.get_llm(model="gpt-3.5-turbo")
    assert llm.model_name == "gpt-3.5-turbo"


@patch("src.core.validators.ApiKeyValidator.validate_openai")
def test_get_llm_missing_key(mock_validate: MagicMock) -> None:
    from src.core.config import Settings
    from src.core.llm import LLMProvider
    mock_settings = MagicMock(spec=Settings)
    mock_settings.openai_api_key = None
    # Updated error message constant in Cycle 06
    with pytest.raises(ValueError, match="LLM configuration invalid"):
        provider = LLMProvider(settings=mock_settings)
        llm_factory = LLMFactory(provider=provider)
        llm_factory.get_llm()
