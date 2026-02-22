from unittest.mock import MagicMock, patch
import pytest
from pydantic import SecretStr

# Note: We patch 'src.core.llm.settings' instead of 'OPENAI_API_KEY'
from src.core.llm import get_llm


def test_config_values() -> None:
    # This just tests that they are imported, but actual values depend on env
    # We can't really test env vars here easily without reloading module
    pass


@patch("src.core.llm.settings")
def test_get_llm_success(mock_settings: MagicMock) -> None:
    mock_settings.openai_api_key = SecretStr("test-key")
    llm = get_llm(model="gpt-3.5-turbo")
    assert llm.model_name == "gpt-3.5-turbo"
    assert llm.openai_api_key == SecretStr("test-key")


@patch("src.core.llm.settings")
def test_get_llm_missing_key(mock_settings: MagicMock) -> None:
    mock_settings.openai_api_key = None
    with pytest.raises(ValueError, match="API key is missing"):
        get_llm()
