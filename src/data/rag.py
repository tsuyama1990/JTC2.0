import functools
import logging
import os
import time
from pathlib import Path

import pybreaker
from llama_index.core import Document, VectorStoreIndex, load_index_from_storage
from llama_index.core import Settings as LlamaSettings
from llama_index.core.storage.storage_context import StorageContext
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

from src.core.config import get_settings
from src.core.constants import (
    ERR_CIRCUIT_OPEN,
    ERR_PATH_TRAVERSAL,
    ERR_RAG_INDEX_SIZE,
    ERR_RAG_QUERY_TOO_LARGE,
    ERR_RAG_TEXT_TOO_LARGE,
)
from src.core.exceptions import ConfigurationError, NetworkError, ValidationError

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=1)
def _get_dir_size_iterative(path: str, limit: int) -> int:
    """
    Iterative directory size calculation with early exit and caching.
    Uses os.scandir for efficiency.
    """
    total = 0
    stack = [path]

    while stack:
        current_path = stack.pop()
        try:
            with os.scandir(current_path) as it:
                for entry in it:
                    if entry.is_file():
                        total += entry.stat().st_size
                    elif entry.is_dir(follow_symlinks=False):
                        stack.append(entry.path)

                    if total > limit:
                        return total
        except OSError as e:
            logger.warning(f"Error scanning index directory {current_path}: {e}")

    return total


class RAG:
    """
    Retrieval-Augmented Generation (RAG) engine using LlamaIndex.
    """

    def __init__(self, persist_dir: str | None = None) -> None:
        self.settings = get_settings()
        # Security: Validate persist_dir path
        raw_path = persist_dir or self.settings.rag_persist_dir
        self.persist_dir = self._validate_path(raw_path)

        # Circuit Breaker
        self.breaker = pybreaker.CircuitBreaker(
            fail_max=self.settings.circuit_breaker_fail_max,
            reset_timeout=self.settings.circuit_breaker_reset_timeout,
        )

        # Simple Rate Limiting State
        self._last_call_time = 0.0
        self._min_interval = 0.1 # 10 requests/second max locally initiated

        self.index: VectorStoreIndex | None = None
        self._init_llama()

    def _validate_path(self, path_str: str) -> str:
        """
        Ensure persist directory is safe and absolute.
        Uses strict allowlist and pathlib.is_relative_to for security.
        """
        if not path_str or not isinstance(path_str, str):
            msg = "Path must be a non-empty string."
            raise ConfigurationError(msg)

        try:
            path = Path(path_str).resolve()
        except Exception as e:
            msg = f"Invalid path format: {e}"
            raise ConfigurationError(msg) from e

        cwd = Path.cwd().resolve()

        # Strict allowlist: Must be contained within specific project folders
        # We allow 'data', 'vector_store' (default), and 'tests' (for testing)
        allowed_parents = [
            cwd / "data",
            cwd / "vector_store",
            cwd / "tests",
        ]

        is_safe = False
        for parent in allowed_parents:
            try:
                if path.is_relative_to(parent):
                    is_safe = True
                    break
            except ValueError:
                continue

        if not is_safe:
             logger.error(f"Path Traversal Attempt: {path} is not in allowed parents {allowed_parents}")
             raise ConfigurationError(ERR_PATH_TRAVERSAL)

        return str(path)

    def _init_llama(self) -> None:
        """Initialize LlamaIndex settings and load existing index if available."""
        if not self.settings.openai_api_key:
            raise ConfigurationError(self.settings.errors.config_missing_openai)

        api_key_str = self.settings.openai_api_key.get_secret_value()

        LlamaSettings.llm = OpenAI(model=self.settings.llm_model, api_key=api_key_str)
        LlamaSettings.embed_model = OpenAIEmbedding(api_key=api_key_str)

        # Only attempt to load if the directory exists and has files
        if Path(self.persist_dir).exists():
            self._load_existing_index()

    def _load_existing_index(self) -> None:
        """Load the index from storage if it exists and is valid."""
        # Use iterator to check for emptiness without loading list
        path_obj = Path(self.persist_dir)
        if not any(path_obj.iterdir()):
            logger.info(
                f"Persist directory {self.persist_dir} exists but is empty. Initializing new index."
            )
            self.index = None
            return

        # Critical: Check size BEFORE loading storage context logic
        self._check_index_size()

        try:
            storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)
            logger.info(f"Loading index from {self.persist_dir}...")
            self.index = load_index_from_storage(storage_context)  # type: ignore[assignment]

        except Exception:
            logger.exception("Failed to load index from %s", self.persist_dir)
            self.index = None
            # Allow continuing with fresh index unless it was a MemoryError (caught above)

    def _check_index_size(self) -> None:
        """
        Check if the index is too large and raise error if unsafe.
        Uses optimized scanning with early termination.
        """
        limit_mb = self.settings.rag_max_index_size_mb
        limit_bytes = limit_mb * 1024 * 1024

        size = _get_dir_size_iterative(self.persist_dir, limit_bytes)
        if size > limit_bytes:
            msg = ERR_RAG_INDEX_SIZE.format(limit=limit_mb)
            logger.error(msg)
            raise MemoryError(msg)

    def _rate_limit(self) -> None:
        """Simple blocking rate limiter."""
        current = time.time()
        elapsed = current - self._last_call_time
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call_time = time.time()

    def ingest_text(self, text: str, source: str) -> None:
        """
        Ingest text into the vector store in-memory.
        Uses batch insertion and strict validation.
        """
        self._rate_limit()

        # Strict Input Validation
        if not text or not isinstance(text, str):
            msg = "Text must be a non-empty string."
            raise ValidationError(msg)

        max_len = self.settings.rag_max_document_length
        if len(text) > max_len:
            msg = ERR_RAG_TEXT_TOO_LARGE.format(size=len(text))
            raise ValidationError(msg)

        if not source or not isinstance(source, str):
            msg = "Source must be a non-empty string."
            raise ValidationError(msg)

        chunk_size = self.settings.rag_chunk_size

        # Chunking
        if len(text) > chunk_size:
            logger.info(f"Text too large ({len(text)} chars). Chunking...")
            chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
        else:
            chunks = [text]

        documents = [
            Document(text=chunk, metadata={"source": source, "chunk_index": i})
            for i, chunk in enumerate(chunks)
        ]

        try:
            if self.index is None:
                self.index = VectorStoreIndex.from_documents(documents)
            else:
                for doc in documents:
                    self.index.insert(doc)
        except Exception as e:
            logger.exception("Failed to ingest document from %s", source)
            msg = f"Ingestion failed: {e}"
            raise RuntimeError(msg) from e

    def persist_index(self) -> None:
        """Persist the index to disk."""
        if self.index:
            self.index.storage_context.persist(persist_dir=self.persist_dir)
            logger.info(f"Index persisted to {self.persist_dir}")

    def query(self, question: str) -> str:
        """
        Query the index for relevant context.
        """
        self._rate_limit()

        if not isinstance(question, str):
            msg = "Query must be a string."
            raise TypeError(msg)

        if not question.strip():
            msg = "Query cannot be empty."
            raise ValueError(msg)

        max_len = self.settings.rag_max_query_length
        if len(question) > max_len:
            msg = ERR_RAG_QUERY_TOO_LARGE.format(size=len(question))
            raise ValidationError(msg)

        question = question.strip()

        try:
            return self.breaker.call(self._query_impl, question)
        except pybreaker.CircuitBreakerError as e:
            logger.exception("Circuit breaker open.")
            raise NetworkError(ERR_CIRCUIT_OPEN) from e

    def _query_impl(self, question: str) -> str:
        if self.index is None:
            return "No data available."

        query_engine = self.index.as_query_engine()
        response = query_engine.query(question)
        return str(response)
