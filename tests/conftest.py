import os
from unittest.mock import MagicMock

import pytest

# Centralized dummy keys to avoid hardcoding in multiple files
# Usage: @patch.dict(os.environ, DUMMY_ENV_VARS)
DUMMY_ENV_VARS = {
    "OPENAI_API_KEY": "sk-dummytestkeylongenoughforvalidation012345",
    "TAVILY_API_KEY": "tvly-dummytestkeylongenoughforvalidation",
    "V0_API_KEY": "v0-dummytestkeylongenoughforvalidation",
}

# Apply dummy env vars immediately for module-level imports during collection
os.environ.update(DUMMY_ENV_VARS)


@pytest.fixture
def mock_llm_factory() -> MagicMock:
    return MagicMock()


@pytest.fixture
def dummy_env() -> dict[str, str]:
    return DUMMY_ENV_VARS
