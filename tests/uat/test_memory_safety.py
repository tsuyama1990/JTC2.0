"""
UAT for Memory Safety and Scalability (Cycle 3 Check).
"""

import itertools
import os
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.core.config import get_settings
from src.data.rag import RAG
from src.domain_models.common import LazyIdeaIterator
from src.domain_models.lean_canvas import LeanCanvas
from tests.conftest import DUMMY_ENV_VARS


@pytest.fixture
def temp_rag_dir(tmp_path: Path) -> str:
    """Provide a temporary directory for RAG index."""
    d = tmp_path / "rag_test"
    d.mkdir()
    return str(d)


@patch.dict(os.environ, DUMMY_ENV_VARS)
def test_lazy_iterator_safety_limit() -> None:
    """
    Verify that LazyIdeaIterator raises StopIteration if the safety limit is exceeded.
    """
    def infinite_generator() -> Iterator[LeanCanvas]:
        """Yields infinite sequence."""
        i = 0
        while True:
            yield LeanCanvas(
                id=i,
                title=f"Idea {i}",
                problem="Problem text is long enough",
                customer_segments="Segments text is long enough",
                unique_value_prop="UVP text is long enough",
                solution="Solution text is long enough",
            )
            i += 1

    lazy_iter = LazyIdeaIterator(infinite_generator())
    # Override limit for test speed
    lazy_iter._max_items = 100

    # Consume up to limit using islice to prevent OOM in test
    list(itertools.islice(lazy_iter, 100))

    # Next call should fail
    with pytest.raises(StopIteration, match="Safety limit reached"):
        next(lazy_iter)


@patch.dict(os.environ, DUMMY_ENV_VARS)
def test_rag_large_index_prevention(temp_rag_dir: str) -> None:
    """
    Verify RAG prevents loading an index that exceeds the size limit.
    """
    get_settings.cache_clear()

    # Create a dummy large file
    p = Path(temp_rag_dir) / "large_index_file.bin"
    # Create 2MB file
    with p.open("wb") as f:
        f.write(b"\0" * (2 * 1024 * 1024))

    # We must patch _validate_path because temp_rag_dir (from pytest tmp_path) is usually in /tmp
    # which is outside project root, so _validate_path would fail before size check.
    # We allow the path for this test.
    with (
        patch("src.data.rag.RAG._validate_path", side_effect=lambda x: str(Path(x).resolve())),
        patch.object(get_settings(), "rag_max_index_size_mb", 1),
        pytest.raises(RuntimeError, match="RAG Index Load Error"),
    ):
        # Expect RuntimeError because _load_existing_index catches MemoryError and re-raises RuntimeError
        # (or whatever RAG raises now)
        RAG(persist_dir=temp_rag_dir)


@patch.dict(os.environ, DUMMY_ENV_VARS)
def test_rag_ingest_chunking(temp_rag_dir: str) -> None:
    """
    Verify that ingestion chunks large text.
    """
    get_settings.cache_clear()

    # Patch _validate_path
    with (
        patch("src.data.rag.RAG._validate_path", side_effect=lambda x: str(Path(x).resolve())),
        patch.object(get_settings(), "rag_chunk_size", 10),
    ):
        rag = RAG(persist_dir=temp_rag_dir)
        # Mock index to verify insertion calls
        rag.index = MagicMock()

        long_text = "This is a very long text that should be chunked."
        rag.ingest_text(long_text, source="test")

        # Length 48, chunk 10 -> ceil(4.8) -> 5 chunks
        assert rag.index.insert.call_count == 5
