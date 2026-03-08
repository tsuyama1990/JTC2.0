import os
from unittest.mock import MagicMock, patch

import pytest

# Centralized dummy keys to avoid hardcoding in multiple files
# Usage: @patch.dict(os.environ, DUMMY_ENV_VARS)
DUMMY_ENV_VARS = {
    "OPENAI_API_KEY": "sk-dummy-test-key-long-enough-for-validation",
    "TAVILY_API_KEY": "tvly-dummy-test-key-long-enough-for-validation",
    "V0_API_KEY": "v0-dummy-test-key-long-enough-for-validation",
    "V0_API_URL": "https://api.v0.dev/test",
}

# Apply dummy env vars immediately for module-level imports during collection
os.environ.update(DUMMY_ENV_VARS)

# Globally patch urllib.request.urlopen to prevent network calls during settings instantiation
patcher = patch("urllib.request.urlopen")
mock_urlopen = patcher.start()
mock_response = MagicMock()
mock_response.status = 200
mock_urlopen.return_value.__enter__.return_value = mock_response


@pytest.fixture
def mock_llm_factory() -> MagicMock:
    return MagicMock()


@pytest.fixture
def dummy_env() -> dict[str, str]:
    return DUMMY_ENV_VARS
