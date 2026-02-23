from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest

try:
    from src.data.rag import RAG
except ImportError:
    RAG = None  # type: ignore


@pytest.fixture
def mock_settings() -> Generator[MagicMock, None, None]:
    with patch("src.data.rag.get_settings") as mock:
        mock.return_value.openai_api_key.get_secret_value.return_value = "sk-test"
        mock.return_value.llm_model = "gpt-4o"
        yield mock

@pytest.fixture
def mock_llama_index() -> Generator[dict[str, MagicMock], None, None]:
    with patch("src.data.rag.VectorStoreIndex") as mock_index, \
         patch("src.data.rag.Document") as mock_doc, \
         patch("src.data.rag.StorageContext") as mock_storage, \
         patch("src.data.rag.load_index_from_storage") as mock_load:
        yield {
            "index": mock_index,
            "doc": mock_doc,
            "storage": mock_storage,
            "load": mock_load
        }

@pytest.mark.skipif(RAG is None, reason="RAG module not implemented yet")
def test_rag_initialization(mock_settings: MagicMock, mock_llama_index: dict[str, MagicMock]) -> None:
    """Test RAG initialization."""
    rag = RAG()
    assert rag.index is None
    # Depending on implementation, it might load existing index or start empty.

@pytest.mark.skipif(RAG is None, reason="RAG module not implemented yet")
def test_rag_ingest_text(mock_settings: MagicMock, mock_llama_index: dict[str, MagicMock]) -> None:
    """Test text ingestion."""
    rag = RAG()
    text = "Customer says: I hate this."
    rag.ingest_text(text, source="interview.txt")

    mock_llama_index["doc"].assert_called()
    # Check that index was created or updated
    # This is a bit loose until implementation is clearer, but good enough for TDD start.

@pytest.mark.skipif(RAG is None, reason="RAG module not implemented yet")
def test_rag_query(mock_settings: MagicMock, mock_llama_index: dict[str, MagicMock]) -> None:
    """Test querying the index."""
    rag = RAG()
    # Mock the index and query engine
    mock_query_engine = MagicMock()
    mock_response = MagicMock()
    # Explicitly set __str__ to a MagicMock so we can set return_value
    mock_response.__str__ = MagicMock(return_value="The customer hates it.")  # type: ignore[method-assign]
    mock_query_engine.query.return_value = mock_response

    # Manually set the index mock
    rag.index = MagicMock()
    rag.index.as_query_engine.return_value = mock_query_engine

    response = rag.query("What does the customer hate?")
    assert response == "The customer hates it."
    rag.index.as_query_engine.assert_called_once()
