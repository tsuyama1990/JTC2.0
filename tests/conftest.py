import os
import secrets
import string
from unittest.mock import MagicMock

import pytest


def generate_dummy_openai_key() -> str:
    """Generate a random OpenAI API key matching ^sk-[a-zA-Z0-9]{48}$ for testing."""
    chars = string.ascii_letters + string.digits
    random_part = "".join(secrets.choice(chars) for _ in range(48))
    return f"sk-{random_part}"

def generate_dummy_tavily_key() -> str:
    """Generate a random Tavily API key for testing."""
    chars = string.ascii_letters + string.digits
    random_part = "".join(secrets.choice(chars) for _ in range(24))
    return f"tvly-{random_part}"

def generate_dummy_v0_key() -> str:
    """Generate a random V0 API key for testing."""
    chars = string.ascii_letters + string.digits
    random_part = "".join(secrets.choice(chars) for _ in range(24))
    return f"v0-{random_part}"

# Centralized dummy keys to avoid hardcoding in multiple files
# Usage: @patch.dict(os.environ, DUMMY_ENV_VARS)
DUMMY_ENV_VARS = {
    "OPENAI_API_KEY": generate_dummy_openai_key(),
    "TAVILY_API_KEY": generate_dummy_tavily_key(),
    "V0_API_KEY": generate_dummy_v0_key(),
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
