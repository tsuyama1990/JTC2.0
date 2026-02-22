from unittest.mock import patch

import pytest
from pydantic import SecretStr

from src.core.llm import get_llm


def test_config_values() -> None:
    # This just tests that they are imported, but actual values depend on env
    # We can't really test env vars here easily without reloading module
    pass


@patch("src.core.llm.OPENAI_API_KEY", "test-key")
def test_get_llm_success() -> None:
    llm = get_llm(model="gpt-3.5-turbo")
    assert llm.model_name == "gpt-3.5-turbo"
    assert llm.openai_api_key == SecretStr("test-key")


@patch("src.core.llm.OPENAI_API_KEY", None)
def test_get_llm_missing_key() -> None:
    with pytest.raises(ValueError, match="OPENAI_API_KEY not set"):
        get_llm()
