import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.core.config import AgentConfig, SimulationConfig, get_settings


def test_config_loading_success() -> None:
    """Test successful configuration loading."""
    with patch.dict(
        os.environ, {"OPENAI_API_KEY": "sk-123", "TAVILY_API_KEY": "tvly-123", "V0_API_KEY": "v0-123"}
    ):
        get_settings.cache_clear()
        settings = get_settings()
        assert settings.openai_api_key is not None
        assert settings.openai_api_key.get_secret_value() == "sk-123"
        assert settings.tavily_api_key is not None
        assert settings.tavily_api_key.get_secret_value() == "tvly-123"
        assert settings.v0_api_key is not None
        assert settings.v0_api_key.get_secret_value() == "v0-123"


def test_config_missing_openai_key() -> None:
    """Test validation error when OpenAI key is missing."""
    with patch.dict(os.environ, {}, clear=True):
        # We need to set TAVILY_API_KEY to isolate the OPENAI_API_KEY check
        os.environ["TAVILY_API_KEY"] = "tvly-123"
        get_settings.cache_clear()

        # Validation happens on init
        with pytest.raises(ValueError):
            get_settings()


def test_config_missing_tavily_key() -> None:
    """Test validation error when Tavily key is missing."""
    with patch.dict(os.environ, {}, clear=True):
        os.environ["OPENAI_API_KEY"] = "sk-123"
        get_settings.cache_clear()

        with pytest.raises(ValueError):
             get_settings()


def test_config_caching() -> None:
    """Test that configuration is cached."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-123", "TAVILY_API_KEY": "tvly-123"}):
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
        {"OPENAI_API_KEY": "sk-123", "TAVILY_API_KEY": "tvly-123", "LOG_LEVEL": "INVALID"},
    ):
        get_settings.cache_clear()
        s = get_settings()
        assert s.log_level == "INVALID"


def test_agent_config_validation() -> None:
    """Test validation for AgentConfig."""
    # Valid config
    AgentConfig(role="Test", label="T", color=0, x=1, y=1, w=10, h=10, text_x=1, text_y=1)

    # Invalid color (<0)
    with pytest.raises(ValidationError):
        AgentConfig(role="Test", label="T", color=-1, x=1, y=1, w=10, h=10, text_x=1, text_y=1)

    # Invalid color (>15)
    with pytest.raises(ValidationError):
        AgentConfig(role="Test", label="T", color=16, x=1, y=1, w=10, h=10, text_x=1, text_y=1)

    # Invalid dimension (<=0)
    with pytest.raises(ValidationError):
        AgentConfig(role="Test", label="T", color=0, x=1, y=1, w=0, h=10, text_x=1, text_y=1)


def test_simulation_config_validation() -> None:
    """Test validation for SimulationConfig."""
    # Valid
    config = SimulationConfig(width=160, height=120, fps=30, bg_color=0, text_color=7)
    assert "CPO" in config.agents

    # Invalid FPS
    with pytest.raises(ValidationError):
        SimulationConfig(fps=0)

    # Invalid Resolution
    with pytest.raises(ValidationError):
        SimulationConfig(width=-100)
