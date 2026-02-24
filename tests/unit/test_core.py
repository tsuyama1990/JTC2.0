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
        TAVILY_API_KEY=SecretStr("tvly-12345678901234567890")
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
    mock_settings = mock_get_settings.return_value
    mock_settings.openai_api_key = None
    # Updated error message constant in Cycle 06
    with pytest.raises(ValueError, match="LLM configuration invalid"):
        get_llm()
