from unittest.mock import MagicMock, patch

import pybreaker
import pytest

from src.core.constants import ERR_CIRCUIT_OPEN, ERR_RAG_TEXT_TOO_LARGE
from src.core.exceptions import NetworkError, ValidationError
from src.data.rag import RAG
from tests.conftest import DUMMY_ENV_VARS


@patch.dict("os.environ", DUMMY_ENV_VARS)
def test_rag_circuit_breaker() -> None:
    """Test that the circuit breaker opens and raises NetworkError."""
    rag = RAG(persist_dir="./tests/temp_rag_cb")

    # Mock the internal implementation to raise pybreaker.CircuitBreakerError
    # We must patch the breaker instance itself or the call method
    rag.breaker = MagicMock()
    rag.breaker.call.side_effect = pybreaker.CircuitBreakerError("Open")

    with pytest.raises(NetworkError, match=ERR_CIRCUIT_OPEN):
        rag.query("Test query")


@patch.dict("os.environ", DUMMY_ENV_VARS)
def test_rag_input_validation() -> None:
    """Test input validation for RAG methods."""
    rag = RAG(persist_dir="./tests/temp_rag_val")

    # Text too large
    large_text = "a" * (rag.settings.rag_max_document_length + 1)
    with pytest.raises(ValidationError, match="Text too large"):
        rag.ingest_text(large_text, "source")

    # Query too large
    large_query = "a" * (rag.settings.rag_max_query_length + 1)
    with pytest.raises(ValidationError, match="Query too large"):
        rag.query(large_query)

    # Empty inputs
    with pytest.raises(TypeError, match="Query must be a string"):
        rag.query(None)  # type: ignore

    with pytest.raises(ValueError, match="Query cannot be empty"):
        rag.query("   ")


@patch.dict("os.environ", DUMMY_ENV_VARS)
def test_error_formatting() -> None:
    """Verify error messages are formatted correctly."""
    # This checks the constants logic implicitly via usage
    msg = ERR_RAG_TEXT_TOO_LARGE.format(size=123)
    assert "Text too large (123 chars)" in msg
