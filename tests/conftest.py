from unittest.mock import MagicMock

import pytest

# Centralized dummy keys to avoid hardcoding in multiple files
# Usage: @patch.dict(os.environ, DUMMY_ENV_VARS)
DUMMY_ENV_VARS = {
    "OPENAI_API_KEY": "sk-dummy-test-key",
    "TAVILY_API_KEY": "tvly-dummy-test-key",
    "V0_API_KEY": "v0-dummy-test-key",
}

@pytest.fixture
def mock_llm_factory() -> MagicMock:
    return MagicMock()

@pytest.fixture
def dummy_env() -> dict[str, str]:
    return DUMMY_ENV_VARS
