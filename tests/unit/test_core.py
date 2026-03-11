from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr

# Note: We patch 'src.core.llm.settings' instead of 'OPENAI_API_KEY'
from src.core.llm import get_llm


def test_config_values() -> None:
    """Test that default settings are loaded correctly."""
    from src.core.config import Settings

    # Use environment variable naming for Pydantic BaseSettings init
    # Must also include required V0_API_URL now
    s = Settings(
        OPENAI_API_KEY=SecretStr("sk-" + "a" * 48),
        TAVILY_API_KEY=SecretStr("tvly-" + "b" * 24),
        V0_API_URL="https://api.v0.dev/chat",
    )
    assert s.llm_model == "gpt-4o"
    assert s.search_max_results == 5
    assert s.openai_api_key == SecretStr("sk-" + "a" * 48)


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
