
import re

import pytest

from src.core.constants import ERR_PATH_TRAVERSAL
from src.core.exceptions import ConfigurationError
from src.data.rag import RAG


def test_rag_path_traversal() -> None:
    """Verify that RAG prevents path traversal."""
    # We pass a path that is clearly outside the project root (e.g., /tmp or /etc)
    # assuming the project root is not /

    unsafe_path = "/etc/passwd"

    # We assume _validate_path is called in __init__
    # We use re.escape to ensure the constant string is treated literally in regex match
    with pytest.raises(ConfigurationError, match=re.escape(ERR_PATH_TRAVERSAL)):
        RAG(persist_dir=unsafe_path)
