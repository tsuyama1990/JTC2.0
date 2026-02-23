import os
from unittest.mock import patch

import pytest

from src.core.config import get_settings


def test_config_loading_success() -> None:
    """Test successful configuration loading."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-123", "TAVILY_API_KEY": "tv-123"}):
        get_settings.cache_clear()
        settings = get_settings()
        assert settings.openai_api_key is not None
        assert settings.openai_api_key.get_secret_value() == "sk-123"
        assert settings.tavily_api_key is not None
        assert settings.tavily_api_key.get_secret_value() == "tv-123"


def test_config_missing_openai_key() -> None:
    """Test validation error when OpenAI key is missing."""
    with patch.dict(os.environ, {}, clear=True):
        # We need to set TAVILY_API_KEY to isolate the OPENAI_API_KEY check
        os.environ["TAVILY_API_KEY"] = "tv-123"
        get_settings.cache_clear()

        # NOTE: Since we relaxed the validator to check for runtime usage,
        # simply initializing Settings shouldn't fail.
        # But explicitly calling validate_api_keys() SHOULD fail.
        s = get_settings()
        with pytest.raises(ValueError, match="is missing"):
            s.validate_api_keys()


def test_config_missing_tavily_key() -> None:
    """Test validation error when Tavily key is missing."""
    with patch.dict(os.environ, {}, clear=True):
        os.environ["OPENAI_API_KEY"] = "sk-123"
        get_settings.cache_clear()
        s = get_settings()
        with pytest.raises(ValueError, match="is missing"):
            s.validate_api_keys()


def test_config_caching() -> None:
    """Test that configuration is cached."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-123", "TAVILY_API_KEY": "tv-123"}):
        get_settings.cache_clear()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2  # Same object instance


def test_invalid_log_level() -> None:
    """Test loading with invalid log level (although Pydantic might coerce it)."""
    # Assuming standard logging levels, but pydantic might just accept string unless Enum used.
    # BaseSettings allows extra fields to be ignored by default in our config.
    with patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "sk-123", "TAVILY_API_KEY": "tv-123", "LOG_LEVEL": "INVALID"},
    ):
        get_settings.cache_clear()
        s = get_settings()
        assert s.log_level == "INVALID"
