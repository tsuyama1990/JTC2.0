import logging
import os
import time
from collections import deque
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from functools import lru_cache
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
    ERR_PATH_TRAVERSAL,
    ERR_RAG_INDEX_SIZE,
    ERR_RAG_NO_DATA_AVAILABLE,
    ERR_RAG_QUERY_TOO_LARGE,
    ERR_RAG_TEXT_TOO_LARGE,
)
from src.core.exceptions import ConfigurationError, NetworkError, ValidationError
from src.core.utils import AsyncRateLimiter, sanitize_text
from src.domain_models.transcript import Transcript

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _scan_dir_size_cached(path: str, depth_limit: int | None = None, ttl_hash: int = 0) -> int:
    """
    Cached version of directory size calculation.
    ttl_hash is a trick to invalidate cache by passing a changing value (like time // 60).
    """
    return _scan_dir_size(path, depth_limit)


def _scan_dir_size(path: str, depth_limit: int | None = None) -> int:
    """
    Calculate directory size using an iterative approach with explicit stack management,
    configurable depth limits, and symlink loop detection.

    Args:
        path: Path to scan.
        depth_limit: Maximum recursion depth.

    Returns:
        Total size in bytes.
    """
    if depth_limit is None:
        depth_limit = get_settings().rag.scan_depth_limit

    if depth_limit is not None and depth_limit <= 0:
        msg = "depth_limit must be positive"
        raise ValueError(msg)

    total_size = 0
    file_count = 0
    max_files = get_settings().rag.max_files

    # Path validation before scanning
    try:
        base_path = Path(path).resolve(strict=True)
        cwd = Path.cwd().resolve(strict=True)
        allowed_rel_paths = get_settings().rag.allowed_paths
        allowed_parents = [(cwd / p).resolve() for p in allowed_rel_paths]

        is_safe = any(base_path.is_relative_to(parent) for parent in allowed_parents)
        if not is_safe:
            logger.error(ERR_PATH_TRAVERSAL)
            raise ConfigurationError(ERR_PATH_TRAVERSAL)
    except OSError as e:
        logger.warning(f"Failed to resolve path: {path}")
        msg = f"Invalid path: {e}"
        raise ConfigurationError(msg) from e

    # Stack stores tuples of (current_path, current_depth)
    stack = deque([(str(base_path), 0)])
    visited_realpaths = set()

    while stack:
        current_path, current_depth = stack.pop()

        if current_depth > depth_limit:
            continue

        try:
            real_path = os.path.realpath(current_path)
            if real_path in visited_realpaths:
                continue
            visited_realpaths.add(real_path)

            with os.scandir(current_path) as it:
                for entry in it:
                    try:
                        if entry.is_symlink():
                            continue # explicitly skip symlinks to prevent loops

                        if entry.is_file(follow_symlinks=False):
                            try:
                                stat_res = entry.stat(follow_symlinks=False)
                                total_size += stat_res.st_size
                                file_count += 1
                            except OSError as e:
                                logger.warning(f"Error stating file {entry.path}: {e}")
                                continue

                            if file_count > max_files:
                                logger.warning(
                                    f"Scan file limit ({max_files}) reached. Returning partial size."
                                )
                                return total_size
                        elif entry.is_dir(follow_symlinks=False):
                            stack.append((entry.path, current_depth + 1))
                    except PermissionError:
                        logger.warning(f"Permission denied accessing entry: {entry.name}")
                    except OSError as e:
                        logger.warning(f"OS error accessing entry: {entry.name}, {e}")

        except PermissionError:
            logger.warning(f"Permission denied scanning directory {current_path}")
        except OSError as e:
            logger.warning(f"Error scanning index directory {current_path}: {e}")

    return total_size


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
        raw_path = persist_dir or self.settings.rag.persist_dir
        self.persist_dir = self._validate_path(raw_path)

        # Ensure the directory exists or can be created
        try:
            Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            msg = f"Failed to access or create persist directory at {self.persist_dir}: {e}"
            raise ConfigurationError(msg) from e

        # Circuit Breaker
        self.breaker = pybreaker.CircuitBreaker(
            fail_max=self.settings.resiliency.circuit_breaker_fail_max,
            reset_timeout=self.settings.resiliency.circuit_breaker_reset_timeout,
        )

        # Rate Limiting State
        self._rate_limiter = AsyncRateLimiter(self.settings.rag.rate_limit_interval)

        # Incremental Size Tracking
        self._current_index_size = 0
        if Path(self.persist_dir).exists():
            # Use cached scan
            self._current_index_size = _scan_dir_size_cached(
                self.persist_dir,
                depth_limit=self.settings.rag.scan_depth_limit,
                ttl_hash=int(time.time() // 60),  # Refresh every minute
            )

        self.index: VectorStoreIndex | None = None
        self._init_llama()

    def _validate_path(self, path_str: str) -> str:
        """
        Ensure persist directory is safe and absolute using atomic path validation.
        """
        if not isinstance(path_str, str) or not path_str.strip():
            msg = "Path must be a non-empty string."
            raise ConfigurationError(msg)

        try:
            cwd = Path.cwd().resolve(strict=True)
            allowed_rel_paths = self.settings.rag.allowed_paths
            allowed_parents = [(cwd / p).resolve() for p in allowed_rel_paths]

            # Use strict=True to prevent TOCTOU and canonicalize path
            try:
                path = Path(path_str).resolve(strict=True)
            except FileNotFoundError:
                # If path doesn't exist, we resolve its parent to check traversal
                path = Path(path_str).resolve(strict=False)
                if not any(path.is_relative_to(parent) for parent in allowed_parents):
                    logger.exception(ERR_PATH_TRAVERSAL)
                    raise ConfigurationError(ERR_PATH_TRAVERSAL) from None
                return str(path)

            if path.is_symlink():
                msg = "Symlinks not allowed in persist_dir."
                raise ConfigurationError(msg)
            if not path.is_dir():
                msg = f"Path must be a directory: {path_str}"
                raise ConfigurationError(msg)

            # Strict traversal check using canonical paths
            if not any(path.is_relative_to(parent) for parent in allowed_parents):
                logger.error(ERR_PATH_TRAVERSAL)
                raise ConfigurationError(ERR_PATH_TRAVERSAL)

            return str(path)
        except ConfigurationError:
            raise
        except Exception as e:
            msg = f"Invalid path format or non-existent parent: {e}"
            raise ConfigurationError(msg) from e

    def _init_llama(self) -> None:
        """Initialize LlamaIndex settings and load existing index if available."""
        if not self.settings.openai_api_key:
            raise ConfigurationError(self.settings.errors.config_missing_openai)

        api_key_str = self.settings.openai_api_key.get_secret_value()

        LlamaSettings.llm = OpenAI(model=self.settings.llm_model, api_key=api_key_str)
        LlamaSettings.embed_model = OpenAIEmbedding(api_key=api_key_str)

        if Path(self.persist_dir).exists():
            self._load_existing_index()

    def _load_existing_index(self) -> None:
        """Load the index from storage if it exists and is valid."""
        self._check_index_size_limit()

        try:
            if not any(True for _ in os.scandir(self.persist_dir)):
                logger.info(
                    f"Persist directory {self.persist_dir} exists but is empty. Initializing new index."
                )
                self.index = None
                return
        except OSError:
            self.index = None
            return

        try:
            storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)
            logger.info(f"Loading index from {self.persist_dir}...")
            self.index = load_index_from_storage(storage_context)  # type: ignore[assignment]

        except Exception:
            logger.exception("Failed to load index from %s", self.persist_dir)
            self.index = None

    def _check_index_size_limit(self) -> None:
        """Check if the tracked index size is too large."""
        limit_mb = self.settings.rag.max_index_size_mb
        limit_bytes = limit_mb * 1024 * 1024

        if self._current_index_size > limit_bytes:
            logger.error(ERR_RAG_INDEX_SIZE)
            raise MemoryError(ERR_RAG_INDEX_SIZE)

    def _rate_limit(self) -> None:
        """Wait synchronously according to the configured rate limit."""
        self._rate_limiter.wait_sync()

    def _document_generator(self, request: IngestionRequest) -> Iterator[Document]:
        """
        Yield documents from request content one by one.
        Tracks size updates internally.
        """
        chunk_size = self.settings.rag.chunk_size
        max_doc_len = self.settings.rag.max_document_length
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

            for i in range(0, len(content_part), chunk_size):
                chunk = content_part[i : i + chunk_size]
                size_bytes = len(chunk.encode("utf-8"))
                self._current_index_size += size_bytes
                self._check_index_size_limit()

                yield Document(
                    text=chunk,
                    metadata={"source": request.source, "chunk_index": current_chunk_idx},
                )
                current_chunk_idx += 1

    def ingest_text(self, text: str | Iterator[str], source: str) -> None:
        """
        Ingest text into the vector store.
        Streams documents directly to the index to avoid memory accumulation.
        Uses batched insertion for performance.
        """
        self._rate_limit()

        try:
            request = IngestionRequest(text=text, source=source)
        except Exception as e:
            raise ValidationError(str(e)) from e

        doc_iterator = self._document_generator(request)
        batch_size = self.settings.rag.batch_size

        # Generator that yields batches of documents
        def batch_generator() -> Iterator[list[Document]]:
            batch: list[Document] = []
            for doc in doc_iterator:
                batch.append(doc)
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
            if batch:
                yield batch

        try:
            # If index is None, verify we have at least one doc to init
            batched_docs = batch_generator()

            # Get first batch to initialize
            try:
                first_batch = next(batched_docs)
            except StopIteration:
                return  # Empty input

            if self.index is None:
                self.index = VectorStoreIndex.from_documents(first_batch)
            else:
                self.index.insert_nodes(first_batch)

            # Process remaining batches
            for batch in batched_docs:
                self.index.insert_nodes(batch)

        except Exception as e:
            logger.exception("Failed to ingest document from %s", source)
            msg = f"Ingestion failed: {e}"
            raise RuntimeError(msg) from e

    def ingest_transcript(self, transcript: Transcript) -> None:
        """
        Ingest a transcript object.
        """
        self.ingest_text(transcript.content, source=transcript.source)

    def persist_index(self) -> None:
        """Persist the index to disk."""
        if self.index:
            self.index.storage_context.persist(persist_dir=self.persist_dir)
            logger.info(f"Index persisted to {self.persist_dir}")
            _scan_dir_size_cached.cache_clear()
            self._current_index_size = _scan_dir_size_cached(
                self.persist_dir,
                self.settings.rag.scan_depth_limit,
                ttl_hash=int(time.time() // 60),
            )

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

        question = sanitize_text(question)

        max_len = self.settings.rag.max_query_length
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
            return ERR_RAG_NO_DATA_AVAILABLE

        # Synchronous wait for rate limit (if configured)
        self._rate_limiter.wait_sync()

        timeout = getattr(self.settings.rag, "query_timeout", 30.0)

        future = None
        try:
            query_engine = self.index.as_query_engine()

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(query_engine.query, question)
                response = future.result(timeout=timeout)

            return str(response)

        except FuturesTimeoutError:
            if future is not None:
                future.cancel()
            logger.exception("RAG Query timed out after %s seconds", timeout)
            msg = "Query execution timed out"
            raise RuntimeError(msg) from None
        except Exception as e:
            if future is not None:
                future.cancel()
            logger.exception("LlamaIndex query failed: %s", e.__class__.__name__)
            msg = f"Query execution failed: {e}"
            raise RuntimeError(msg) from e
