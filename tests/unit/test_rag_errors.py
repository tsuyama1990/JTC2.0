from unittest.mock import MagicMock, patch

import pybreaker
import pytest

from src.core.constants import ERR_CIRCUIT_OPEN, ERR_RAG_TEXT_TOO_LARGE, ERR_RAG_INDEX_SIZE
from src.core.exceptions import NetworkError, ValidationError
from src.data.rag import RAG
from tests.conftest import DUMMY_ENV_VARS
import re


@patch.dict("os.environ", DUMMY_ENV_VARS)
def test_rag_circuit_breaker() -> None:
    """Test that the circuit breaker opens and raises NetworkError."""
    rag = RAG(persist_dir="./tests/temp_rag_cb")

    # Mock the internal implementation to raise pybreaker.CircuitBreakerError
    # We must patch the breaker instance itself or the call method
    rag.breaker = MagicMock()
    # Simulate pybreaker behavior: .call raises CircuitBreakerError if open
    rag.breaker.call.side_effect = pybreaker.CircuitBreakerError("Circuit is open")

    with pytest.raises(NetworkError, match=ERR_CIRCUIT_OPEN):
        rag.query("Test query")


@patch.dict("os.environ", DUMMY_ENV_VARS)
def test_rag_memory_limit() -> None:
    """Test that MemoryError is raised when index size exceeds limit."""
    rag = RAG(persist_dir="./tests/temp_rag_mem")

    # Mock settings to have a small limit
    rag.settings.rag_max_index_size_mb = 1 # 1 MB
    limit_bytes = 1 * 1024 * 1024

    # Simulate current index size exceeding limit
    rag._current_index_size = limit_bytes + 100

    # Verify check raises MemoryError
    expected_msg = ERR_RAG_INDEX_SIZE.format(limit=1)

    # We must escape regex characters because the error message contains parens
    with pytest.raises(MemoryError, match=re.escape(expected_msg)):
        rag._check_index_size_limit()

    # Also verify ingest_text triggers it
    # ingest_text wraps exceptions in RuntimeError now
    with pytest.raises(RuntimeError, match="Ingestion failed"):
        # Even with empty text, if size is already over limit, it should check
        rag.ingest_text("some text", "source")


@patch.dict("os.environ", DUMMY_ENV_VARS)
def test_rag_input_validation() -> None:
    """Test input validation for RAG methods."""
    rag = RAG(persist_dir="./tests/temp_rag_val")

    # Text too large
    large_text = "a" * (rag.settings.rag_max_document_length + 1)
    # ingest_text catches ValidationError and raises RuntimeError
    with pytest.raises(RuntimeError, match="Ingestion failed"):
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
