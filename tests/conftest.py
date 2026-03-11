import os
import secrets
from unittest.mock import MagicMock

import pytest

# Centralized dummy keys to avoid hardcoding in multiple files
# Usage: @patch.dict(os.environ, DUMMY_ENV_VARS)
DUMMY_ENV_VARS = {
    "OPENAI_API_KEY": f"sk-{secrets.token_hex(24)}",
    "TAVILY_API_KEY": f"tvly-{secrets.token_hex(24)}",
    "V0_API_KEY": f"v0-{secrets.token_hex(24)}",
    "V0_API_URL": "https://api.v0.dev/chat/completions",
}

# Apply dummy env vars immediately for module-level imports during collection
os.environ.update(DUMMY_ENV_VARS)


@pytest.fixture
def mock_llm_factory() -> MagicMock:
    return MagicMock()


@pytest.fixture
def dummy_env() -> dict[str, str]:
    return DUMMY_ENV_VARS
