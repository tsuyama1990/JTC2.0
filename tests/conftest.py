import os
from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_env_vars() -> Generator[None, None, None]:
    """Dynamically provide test environment variables without hardcoding globally."""
    test_env = {
        "OPENAI_API_KEY": f"sk-{__import__('secrets').token_hex(24)}",
        "TAVILY_API_KEY": f"tvly-{__import__('secrets').token_hex(24)}",
        "V0_API_KEY": f"v0-{__import__('secrets').token_hex(24)}",
        "V0_API_URL": "https://api.v0.dev/chat/completions",
        "RAG_PERSIST_DIR": "./vector_store",
        "RAG_ALLOWED_PATHS": "data,vector_store,tests,./vector_store",
        "LLM_MODEL": "gpt-4o",
        "LOG_LEVEL": "INFO",
        "SIMULATION_TITLE": "JTC Simulation: The Meeting",
        "COLOR_BG": "0",
        "COLOR_TEXT": "7",
        "SIMULATION_WIDTH": "800",
        "SIMULATION_HEIGHT": "600",
        "SIMULATION_FPS": "30",
        "SIMULATION_CHARS_PER_LINE": "32",
        "SIMULATION_LINE_HEIGHT": "10",
        "SIMULATION_DIALOGUE_X": "10",
        "SIMULATION_DIALOGUE_Y": "150",
        "SIMULATION_MAX_Y": "500",
        "SIMULATION_WAITING_MSG": "Waiting for debate...",
        "SIMULATION_TURN_SEQUENCE": '[{"node_name": "pitch", "role": "New Employee", "description": "New Employee Pitch"}]',
        "SIMULATION_CONSOLE_SLEEP": "1.5",
        "SIMULATION_MAX_TURNS": "10",
        "AGENT_POS_NEW_EMP": '{"x": 10, "y": 20, "w": 10, "h": 10, "text_x": 0, "text_y": 0}',
        "COLOR_NEW_EMP": "8",
        "AGENT_POS_FINANCE": '{"x": 50, "y": 20, "w": 10, "h": 10, "text_x": 0, "text_y": 0}',
        "COLOR_FINANCE": "9",
        "AGENT_POS_SALES": '{"x": 90, "y": 20, "w": 10, "h": 10, "text_x": 0, "text_y": 0}',
        "COLOR_SALES": "10",
        "AGENT_POS_CPO": '{"x": 130, "y": 20, "w": 10, "h": 10, "text_x": 0, "text_y": 0}',
        "COLOR_CPO": "11",
        "MIN_ROI_THRESHOLD": "3.0",
        "DEFAULT_CAC": "500.0",
        "DEFAULT_ARPU": "50.0",
        "DEFAULT_CHURN": "0.05",
        "RINGI_SHO_PATH": "RINGI_SHO.md",
        "GOV_SEARCH_QUERY_TEMPLATE": "average CAC churn ARPU LTV for {industry} startups benchmarks",
        "SEARCH_QUERY_TEMPLATE": "emerging business trends and painful problems in {topic}",
        "UI_PAGE_SIZE": "3",
        "NEMAWASHI_MAX_STAKEHOLDERS": "10000",
    }
    with patch.dict(os.environ, test_env, clear=True):
        yield


@pytest.fixture
def mock_llm_factory() -> MagicMock:
    return MagicMock()


@pytest.fixture
def dummy_env(mock_env_vars: None) -> dict[str, str]:
    # Returns the env dict by rebuilding it or capturing it if needed.
    return {
        "OPENAI_API_KEY": f"sk-{__import__('secrets').token_hex(24)}",
        "TAVILY_API_KEY": f"tvly-{__import__('secrets').token_hex(24)}",
        "V0_API_KEY": f"v0-{__import__('secrets').token_hex(24)}",
        "V0_API_URL": "https://api.v0.dev/chat/completions",
        "RAG_PERSIST_DIR": "./vector_store",
        "RAG_ALLOWED_PATHS": "data,vector_store,tests,./vector_store",
        "LLM_MODEL": "gpt-4o",
        "LOG_LEVEL": "INFO",
        "SIMULATION_TITLE": "JTC Simulation: The Meeting",
        "COLOR_BG": "0",
        "COLOR_TEXT": "7",
        "SIMULATION_WIDTH": "800",
        "SIMULATION_HEIGHT": "600",
        "SIMULATION_FPS": "30",
        "SIMULATION_CHARS_PER_LINE": "32",
        "SIMULATION_LINE_HEIGHT": "10",
        "SIMULATION_DIALOGUE_X": "10",
        "SIMULATION_DIALOGUE_Y": "150",
        "SIMULATION_MAX_Y": "500",
        "SIMULATION_WAITING_MSG": "Waiting for debate...",
        "SIMULATION_TURN_SEQUENCE": '[{"node_name": "pitch", "role": "New Employee", "description": "New Employee Pitch"}]',
        "SIMULATION_CONSOLE_SLEEP": "1.5",
        "SIMULATION_MAX_TURNS": "10",
        "AGENT_POS_NEW_EMP": '{"x": 10, "y": 20, "w": 10, "h": 10, "text_x": 0, "text_y": 0}',
        "COLOR_NEW_EMP": "8",
        "AGENT_POS_FINANCE": '{"x": 50, "y": 20, "w": 10, "h": 10, "text_x": 0, "text_y": 0}',
        "COLOR_FINANCE": "9",
        "AGENT_POS_SALES": '{"x": 90, "y": 20, "w": 10, "h": 10, "text_x": 0, "text_y": 0}',
        "COLOR_SALES": "10",
        "AGENT_POS_CPO": '{"x": 130, "y": 20, "w": 10, "h": 10, "text_x": 0, "text_y": 0}',
        "COLOR_CPO": "11",
        "MIN_ROI_THRESHOLD": "3.0",
        "DEFAULT_CAC": "500.0",
        "DEFAULT_ARPU": "50.0",
        "DEFAULT_CHURN": "0.05",
        "RINGI_SHO_PATH": "RINGI_SHO.md",
        "GOV_SEARCH_QUERY_TEMPLATE": "average CAC churn ARPU LTV for {industry} startups benchmarks",
        "SEARCH_QUERY_TEMPLATE": "emerging business trends and painful problems in {topic}",
        "UI_PAGE_SIZE": "3",
        "NEMAWASHI_MAX_STAKEHOLDERS": "10000",
    }
