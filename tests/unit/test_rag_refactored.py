
import pytest

from src.data.rag import RAG


def test_rag_path_traversal() -> None:
    """Verify that RAG prevents path traversal."""
    # We pass a path that is clearly outside the project root (e.g., /tmp or /etc)
    # assuming the project root is not /

    unsafe_path = "/etc/passwd"

    # We assume _validate_path is called in __init__
    # The current RAG implementation raises ValueError with a specific message.
    # Once refactored, it should match ERR_PATH_TRAVERSAL.
    # For now, we just check ValueError.

    with pytest.raises(ValueError, match="Path traversal"):
        RAG(persist_dir=unsafe_path)
