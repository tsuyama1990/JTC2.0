import logging
import os
import time
from collections.abc import Iterator
from pathlib import Path

import pybreaker
from llama_index.core import Document, VectorStoreIndex, load_index_from_storage
from llama_index.core import Settings as LlamaSettings
from llama_index.core.storage.storage_context import StorageContext
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.core.config import get_settings
from src.core.constants import (
    ERR_CIRCUIT_OPEN,
    ERR_RAG_INDEX_SIZE,
    ERR_RAG_QUERY_TOO_LARGE,
    ERR_RAG_TEXT_TOO_LARGE,
)
from src.core.exceptions import ConfigurationError, NetworkError, ValidationError

logger = logging.getLogger(__name__)


def _scan_dir_size(path: str) -> int:
    """
    Calculate directory size iteratively.
    Optimized to use os.scandir which yields DirEntry objects containing cached stat info.
    """
    total = 0
    stack = [path]

    while stack:
        current_path = stack.pop()
        try:
            with os.scandir(current_path) as it:
                for entry in it:
                    if entry.is_file(follow_symlinks=False):
                        # entry.stat() is cached on Linux/Windows for scandir
                        total += entry.stat().st_size
                    elif entry.is_dir(follow_symlinks=False):
                        stack.append(entry.path)
        except OSError as e:
            logger.warning(f"Error scanning index directory {current_path}: {e}")

    return total


class IngestionRequest(BaseModel):
    """
    Request model for ingesting text.
    Supports both full string and streaming iterator for memory efficiency.
    """

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    text: str | Iterator[str]
    source: str = Field(..., min_length=1)

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str | Iterator[str]) -> str | Iterator[str]:
        if isinstance(v, str) and not v:
            msg = "Text must be a non-empty string."
            raise ValueError(msg)
        return v


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
        self._min_interval = 0.1  # 10 requests/second max locally initiated

        # Incremental Size Tracking
        # Calculate once at startup, then track incrementally
        self._current_index_size = 0
        if Path(self.persist_dir).exists():
            self._current_index_size = _scan_dir_size(self.persist_dir)

        self.index: VectorStoreIndex | None = None
        self._init_llama()

    def _validate_path(self, path_str: str) -> str:
        """
        Ensure persist directory is safe and absolute.
        Uses strict allowlist and pathlib.resolve(strict=True) for security.
        """
        if not path_str or not isinstance(path_str, str):
            msg = "Path must be a non-empty string."
            raise ConfigurationError(msg)

        try:
            # resolve(strict=True) checks existence.
            # If path doesn't exist, we check parent.
            path = Path(path_str)
            if path.exists():
                path = path.resolve(strict=True)
            else:
                # If path doesn't exist, verify parent exists and is safe
                # This prevents creating files in arbitrary locations
                parent = path.parent.resolve(strict=True)
                path = parent / path.name
                # Note: path is now absolute but might not exist, which is fine for creation
        except Exception as e:
            msg = f"Invalid path format or non-existent parent: {e}"
            raise ConfigurationError(msg) from e

        cwd = Path.cwd().resolve(strict=True)

        # Load allowed paths from settings
        # These are relative to CWD
        allowed_rel_paths = self.settings.rag_allowed_paths
        allowed_parents = [(cwd / p).resolve() for p in allowed_rel_paths] # Resolve allowed paths too

        is_safe = False
        for parent in allowed_parents:
            try:
                # is_relative_to is safe against traversal if paths are resolved
                if path.is_relative_to(parent):
                    is_safe = True
                    break
            except ValueError:
                continue

        if not is_safe:
            msg = "Path traversal detected in persist_dir. Must be within project root."
            logger.error(f"Path Traversal Attempt: {path} is not in allowed parents {allowed_parents}")
            raise ConfigurationError(msg)

        return str(path)

    def _sanitize_query(self, query: str) -> str:
        """
        Sanitize input query to prevent injection or processing issues.
        - Removes control characters.
        - Trims whitespace.
        - Limits charset to printable.
        """
        # Remove control characters (e.g. null bytes, newlines in middle if undesirable)
        # We allow newlines for multi-line queries but remove other control chars
        # ASCII control chars are 0-31 and 127.
        # We allow tab (9), newline (10), carriage return (13).
        sanitized = "".join(ch for ch in query if (32 <= ord(ch) < 127) or ch in "\t\r\n" or ord(ch) > 127)
        return sanitized.strip()

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
        path_obj = Path(self.persist_dir)
        if not any(path_obj.iterdir()):
            logger.info(
                f"Persist directory {self.persist_dir} exists but is empty. Initializing new index."
            )
            self.index = None
            return

        # Check size before loading
        self._check_index_size_limit()

        try:
            storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)
            logger.info(f"Loading index from {self.persist_dir}...")
            self.index = load_index_from_storage(storage_context)  # type: ignore[assignment]

        except Exception:
            logger.exception("Failed to load index from %s", self.persist_dir)
            self.index = None

    def _check_index_size_limit(self) -> None:
        """
        Check if the tracked index size is too large.
        """
        limit_mb = self.settings.rag_max_index_size_mb
        limit_bytes = limit_mb * 1024 * 1024

        if self._current_index_size > limit_bytes:
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

    def _generate_documents(self, request: IngestionRequest) -> tuple[list[Document], int]:
        """Generate documents from request content."""
        chunk_size = self.settings.rag_chunk_size
        max_doc_len = self.settings.rag_max_document_length
        documents = []
        total_size_added = 0
        current_chunk_idx = 0

        def content_generator() -> Iterator[str]:
            if isinstance(request.text, str):
                if len(request.text) > max_doc_len:
                    raise ValidationError(ERR_RAG_TEXT_TOO_LARGE.format(size=len(request.text)))
                yield request.text
            else:
                yield from request.text

        for content_part in content_generator():
            if not isinstance(content_part, str):
                logger.warning(f"Skipping non-string content in iterator from {request.source}")
                continue

            # Chunking logic
            if len(content_part) > chunk_size:
                chunks = [
                    content_part[i : i + chunk_size]
                    for i in range(0, len(content_part), chunk_size)
                ]
            else:
                chunks = [content_part]

            for chunk in chunks:
                documents.append(
                    Document(
                        text=chunk,
                        metadata={"source": request.source, "chunk_index": current_chunk_idx},
                    )
                )
                current_chunk_idx += 1
                total_size_added += len(chunk.encode("utf-8"))  # Approximate size

        return documents, total_size_added

    def ingest_text(self, text: str | Iterator[str], source: str) -> None:
        """
        Ingest text into the vector store.
        Supports streaming iterators to avoid loading entire dataset into memory.
        """
        self._rate_limit()

        # Validate input using Pydantic
        try:
            request = IngestionRequest(text=text, source=source)
        except Exception as e:
            raise ValidationError(str(e)) from e

        documents, total_size_added = self._generate_documents(request)

        # Incremental Size Check
        self._current_index_size += total_size_added
        self._check_index_size_limit()

        try:
            if not documents:
                return

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
            # Update size from disk to be accurate
            self._current_index_size = _scan_dir_size(self.persist_dir)

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

        # Input Sanitization
        question = self._sanitize_query(question)

        max_len = self.settings.rag_max_query_length
        if len(question) > max_len:
            msg = ERR_RAG_QUERY_TOO_LARGE.format(size=len(question))
            raise ValidationError(msg)

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
