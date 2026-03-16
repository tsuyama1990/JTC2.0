import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.core.config import AgentConfig, SimulationConfig, get_settings


def test_config_loading_success(dummy_env: dict[str, str]) -> None:
    """Test successful configuration loading."""
    with patch.dict(os.environ, dummy_env):
        get_settings.cache_clear()
        settings = get_settings()
        assert settings.openai_api_key is not None
        assert settings.tavily_api_key is not None
        assert settings.v0_api_key is not None


def test_config_missing_openai_key(dummy_env: dict[str, str]) -> None:
    """Test validation error when OpenAI key is missing."""
    env = dummy_env.copy()
    env.pop("OPENAI_API_KEY")
    with patch.dict(os.environ, env, clear=True):
        get_settings.cache_clear()

        # Validation happens on init
        with pytest.raises(ValueError, match=".*"):
            get_settings()


def test_config_missing_tavily_key(dummy_env: dict[str, str]) -> None:
    """Test validation error when Tavily key is missing."""
    env = dummy_env.copy()
    env.pop("TAVILY_API_KEY")
    with patch.dict(os.environ, env, clear=True):
        get_settings.cache_clear()

        with pytest.raises(ValueError, match=".*"):
            get_settings()


def test_config_caching(dummy_env: dict[str, str]) -> None:
    """Test that configuration is cached."""
    with patch.dict(os.environ, dummy_env, clear=True):
        get_settings.cache_clear()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2  # Same object instance


def test_invalid_log_level(dummy_env: dict[str, str]) -> None:
    """Test loading with invalid log level."""
    env = dummy_env.copy()
    env["LOG_LEVEL"] = "INVALID_LEVEL"
    with patch.dict("os.environ", env, clear=True):
        get_settings.cache_clear()
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            get_settings()


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
    config = SimulationConfig(
        SIMULATION_WIDTH=160,
        SIMULATION_HEIGHT=120,
        SIMULATION_FPS=30,
        COLOR_BG=0,
        COLOR_TEXT=7,
        SIMULATION_TITLE="test",
        SIMULATION_CHARS_PER_LINE=10,
        SIMULATION_LINE_HEIGHT=10,
        SIMULATION_DIALOGUE_X=10,
        SIMULATION_DIALOGUE_Y=10,
        SIMULATION_MAX_Y=100,
        SIMULATION_WAITING_MSG="wait",
        SIMULATION_TURN_SEQUENCE='[{"node_name": "pitch", "role": "New Employee", "description": "New Employee Pitch"}]',
        SIMULATION_CONSOLE_SLEEP=1.0,
        SIMULATION_MAX_TURNS=10,
        AGENT_POS_NEW_EMP={"x": 10, "y": 20, "w": 10, "h": 10, "text_x": 0, "text_y": 0},
        AGENT_POS_FINANCE={"x": 50, "y": 20, "w": 10, "h": 10, "text_x": 0, "text_y": 0},
        AGENT_POS_SALES={"x": 90, "y": 20, "w": 10, "h": 10, "text_x": 0, "text_y": 0},
        AGENT_POS_CPO={"x": 130, "y": 20, "w": 10, "h": 10, "text_x": 0, "text_y": 0},
    )
    assert "CPO" in config.agents

    # Invalid FPS
    with pytest.raises(ValidationError):
        SimulationConfig(
            SIMULATION_WIDTH=160,
            SIMULATION_HEIGHT=120,
            SIMULATION_FPS=0,
            COLOR_BG=0,
            COLOR_TEXT=7,
            SIMULATION_TITLE="test",
            SIMULATION_CHARS_PER_LINE=10,
            SIMULATION_LINE_HEIGHT=10,
            SIMULATION_DIALOGUE_X=10,
            SIMULATION_DIALOGUE_Y=10,
            SIMULATION_MAX_Y=100,
            SIMULATION_WAITING_MSG="wait",
            SIMULATION_TURN_SEQUENCE='[{"node_name": "pitch", "role": "New Employee", "description": "New Employee Pitch"}]',
            SIMULATION_CONSOLE_SLEEP=1.0,
            SIMULATION_MAX_TURNS=10,
            AGENT_POS_NEW_EMP={"x": 10, "y": 20, "w": 10, "h": 10, "text_x": 0, "text_y": 0},
            AGENT_POS_FINANCE={"x": 50, "y": 20, "w": 10, "h": 10, "text_x": 0, "text_y": 0},
            AGENT_POS_SALES={"x": 90, "y": 20, "w": 10, "h": 10, "text_x": 0, "text_y": 0},
            AGENT_POS_CPO={"x": 130, "y": 20, "w": 10, "h": 10, "text_x": 0, "text_y": 0},
        )

    # Invalid Resolution
    with pytest.raises(ValidationError):
        SimulationConfig(
            SIMULATION_WIDTH=-100,
            SIMULATION_HEIGHT=120,
            SIMULATION_FPS=30,
            COLOR_BG=0,
            COLOR_TEXT=7,
            SIMULATION_TITLE="test",
            SIMULATION_CHARS_PER_LINE=10,
            SIMULATION_LINE_HEIGHT=10,
            SIMULATION_DIALOGUE_X=10,
            SIMULATION_DIALOGUE_Y=10,
            SIMULATION_MAX_Y=100,
            SIMULATION_WAITING_MSG="wait",
            SIMULATION_TURN_SEQUENCE='[{"node_name": "pitch", "role": "New Employee", "description": "New Employee Pitch"}]',
            SIMULATION_CONSOLE_SLEEP=1.0,
            SIMULATION_MAX_TURNS=10,
            AGENT_POS_NEW_EMP={"x": 10, "y": 20, "w": 10, "h": 10, "text_x": 0, "text_y": 0},
            AGENT_POS_FINANCE={"x": 50, "y": 20, "w": 10, "h": 10, "text_x": 0, "text_y": 0},
            AGENT_POS_SALES={"x": 90, "y": 20, "w": 10, "h": 10, "text_x": 0, "text_y": 0},
            AGENT_POS_CPO={"x": 130, "y": 20, "w": 10, "h": 10, "text_x": 0, "text_y": 0},
        )
