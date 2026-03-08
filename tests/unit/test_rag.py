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
        mock.return_value.rag.persist_dir = "tests/mock_vector_store"
        # Errors
        mock.return_value.errors.config_missing_openai = "Missing API Key"
        # New Config fields
        mock.return_value.rag.chunk_size = 4000
        mock.return_value.rag.max_query_length = 500
        mock.return_value.rag.max_index_size_mb = 500
        mock.return_value.rag.max_document_length = 10000
        mock.return_value.resiliency.circuit_breaker_fail_max = 5
        mock.return_value.resiliency.circuit_breaker_reset_timeout = 60
        mock.return_value.rag.allowed_paths = ["data", "vector_store", "tests"]
        mock.return_value.rag.rate_limit_interval = 0.1
        mock.return_value.rag.scan_depth_limit = 10
        mock.return_value.rag.max_files = 1000
        # Ensure batch size is int
        mock.return_value.rag.batch_size = 100
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


@patch("src.data.rag.RAG._validate_path", return_value="/app/tests")
def test_rag_initialization(
    mock_validate: MagicMock, mock_settings: MagicMock, mock_llama_index: dict[str, MagicMock]
) -> None:
    """Test RAG initialization."""
    mock_settings.return_value.rag.max_index_size_mb = 100
    mock_llama_index["load"].side_effect = Exception("No index")
    rag = RAG(persist_dir="tests")
    assert rag.index is None

@patch("src.data.rag.RAG._validate_path", return_value="/app/tests")
def test_rag_ingest_text(
    mock_validate: MagicMock, mock_settings: MagicMock, mock_llama_index: dict[str, MagicMock]
) -> None:
    """Test text ingestion."""
    mock_settings.return_value.rag.batch_size = 100
    mock_settings.return_value.rag.max_index_size_mb = 100
    mock_llama_index["load"].side_effect = Exception("No index")

    rag = RAG(persist_dir="tests")
    text = "Customer says: I hate this."
    rag.ingest_text(text, source="interview.txt")

    mock_llama_index["doc"].assert_called()
    mock_llama_index["index"].from_documents.assert_called()


@patch("src.data.rag.RAG._validate_path", return_value="/app/tests")
def test_rag_persist_index(
    mock_validate: MagicMock, mock_settings: MagicMock, mock_llama_index: dict[str, MagicMock]
) -> None:
    """Test explicit persist."""
    rag = RAG(persist_dir="tests")
    # Mock index existence
    rag.index = MagicMock()

    rag.persist_index()
    rag.index.storage_context.persist.assert_called()


@patch("src.data.rag.RAG._validate_path", return_value="/app/tests")
def test_rag_query(
    mock_validate: MagicMock, mock_settings: MagicMock, mock_llama_index: dict[str, MagicMock]
) -> None:
    """Test querying the index."""
    rag = RAG(persist_dir="tests")
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


@patch("src.data.rag.RAG._validate_path", return_value="/app/tests")
def test_rag_query_validation(
    mock_validate: MagicMock, mock_settings: MagicMock, mock_llama_index: dict[str, MagicMock]
) -> None:
    """Test query input validation."""
    rag = RAG(persist_dir="tests")

    with pytest.raises(TypeError, match="Query must be a string"):
        rag.query(123)  # type: ignore

    with pytest.raises(ValueError, match="Query cannot be empty"):
        rag.query("   ")
