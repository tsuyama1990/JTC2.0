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
        # Mock rag_persist_dir - must be a valid subdir relative to CWD, e.g. tests/
        mock.return_value.rag_persist_dir = "tests/mock_vector_store"
        # Errors
        mock.return_value.errors.config_missing_openai = "Missing API Key"
        # New Config fields
        mock.return_value.rag_chunk_size = 4000
        mock.return_value.rag_max_query_length = 500
        mock.return_value.rag_max_index_size_mb = 500
        mock.return_value.rag_max_document_length = 10000
        mock.return_value.circuit_breaker_fail_max = 5
        mock.return_value.circuit_breaker_reset_timeout = 60
        mock.return_value.rag_allowed_paths = ["data", "vector_store", "tests"]
        mock.return_value.rag_rate_limit_interval = 0.1
        mock.return_value.rag_scan_depth_limit = 10
        yield mock


@pytest.fixture
def mock_llama_index() -> Generator[dict[str, MagicMock], None, None]:
    with (
        patch("src.data.rag.VectorStoreIndex") as mock_index,
        patch("src.data.rag.Document") as mock_doc,
        patch("src.data.rag.StorageContext") as mock_storage,
        patch("src.data.rag.load_index_from_storage") as mock_load,
        patch("src.data.rag.OpenAI"),
        patch("src.data.rag.OpenAIEmbedding"),
        patch("src.data.rag.LlamaSettings"),
    ):  # Mock Settings to avoid type checks
        yield {"index": mock_index, "doc": mock_doc, "storage": mock_storage, "load": mock_load}


def test_rag_initialization(
    mock_settings: MagicMock, mock_llama_index: dict[str, MagicMock]
) -> None:
    """Test RAG initialization."""
    # We need to ensure the path actually exists for resolve() if we weren't mocking it,
    # but RAG calls resolve().
    # Since we are using a real RAG class, we must provide a path that passes _validate_path.
    # "tests/mock_vector_store" should pass as "tests" is in allowed_parents.

    # We must ensure the directory exists so resolve() works without error if checking existence?
    # Path.resolve() works even if file doesn't exist on Python 3.10+ usually, but strict=True?
    # RAG code uses Path(path_str).resolve() (default strict=False).

    rag = RAG()
    assert rag.index is None
    # Path is resolved to absolute
    from pathlib import Path
    expected = str(Path("tests/mock_vector_store").resolve())
    assert rag.persist_dir == expected


def test_rag_ingest_text(mock_settings: MagicMock, mock_llama_index: dict[str, MagicMock]) -> None:
    """Test text ingestion."""
    rag = RAG()
    text = "Customer says: I hate this."
    rag.ingest_text(text, source="interview.txt")

    mock_llama_index["doc"].assert_called()
    # Ensure it creates an index
    mock_llama_index["index"].from_documents.assert_called()


def test_rag_persist_index(
    mock_settings: MagicMock, mock_llama_index: dict[str, MagicMock]
) -> None:
    """Test explicit persist."""
    rag = RAG()
    # Mock index existence
    rag.index = MagicMock()

    rag.persist_index()
    from pathlib import Path
    expected = str(Path("tests/mock_vector_store").resolve())
    rag.index.storage_context.persist.assert_called_with(persist_dir=expected)


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


def test_rag_query_validation(mock_settings: MagicMock, mock_llama_index: dict[str, MagicMock]) -> None:
    """Test query input validation."""
    rag = RAG()

    with pytest.raises(TypeError, match="Query must be a string"):
        rag.query(123) # type: ignore

    with pytest.raises(ValueError, match="Query cannot be empty"):
        rag.query("   ")
