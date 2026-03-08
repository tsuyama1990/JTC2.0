import logging
import os
import time
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
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
    DEFAULT_MAX_FILES,
    DEFAULT_RAG_BATCH_SIZE,
    DEFAULT_RAG_CHUNK_SIZE,
    DEFAULT_RAG_QUERY_TIMEOUT,
    ERR_CIRCUIT_OPEN,
    ERR_PATH_TRAVERSAL,
    ERR_RAG_INDEX_SIZE,
    ERR_RAG_NO_DATA,
    ERR_RAG_QUERY_FAILED,
    ERR_RAG_QUERY_TIMEOUT,
    ERR_RAG_QUERY_TOO_LARGE,
    ERR_RAG_TEXT_TOO_LARGE,
)
from src.core.exceptions import ConfigurationError, NetworkError, ValidationError
from src.core.utils import (
    calculate_bytes_from_mb,
    clear_rag_cache,
    get_rag_dir_size,
    rate_limit,
    validate_rag_query,
)
from src.domain_models.transcript import Transcript

logger = logging.getLogger(__name__)


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

        # Rate Limiting State
        self._last_call_time = 0.0
        self._min_interval = self.settings.rag_rate_limit_interval

        # Incremental Size Tracking
        self._current_index_size = 0
        if Path(self.persist_dir).exists():
            # Use cached scan
            self._current_index_size = get_rag_dir_size(
                self.persist_dir,
                depth_limit=self.settings.rag_scan_depth_limit,
                max_files=DEFAULT_MAX_FILES,
                ttl_hash=int(time.time() // 60),  # Refresh every minute
            )

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
            path = Path(path_str).resolve(strict=False)
            cwd = Path.cwd().resolve(strict=True)
            allowed_rel_paths = self.settings.rag_allowed_paths
            allowed_parents = [(cwd / p).resolve() for p in allowed_rel_paths]

            path_exists = path.exists()
            is_symlink = path.is_symlink() if path_exists else False
            if path_exists:
                path = path.resolve(strict=True)
        except Exception as e:
            msg = f"Invalid path format or non-existent parent: {e}"
            raise ConfigurationError(msg) from e

        is_safe = False
        for parent in allowed_parents:
            if str(path).startswith(str(parent)):
                is_safe = True
                break

        if not is_safe:
            logger.error(
                f"Path Traversal Attempt: {path} is not in allowed parents {allowed_parents}"
            )
            raise ConfigurationError(ERR_PATH_TRAVERSAL)

        if is_symlink:
            msg = "Symlinks not allowed in persist_dir."
            raise ConfigurationError(msg)

        return str(path)

    def _init_llama(self) -> None:
        """Initialize LlamaIndex settings and load existing index if available."""
        if not self.settings.openai_api_key:
            raise ConfigurationError(self.settings.errors.config_missing_openai)

        api_key_str = self.settings.openai_api_key.get_secret_value()

        LlamaSettings.llm = OpenAI(model=self.settings.llm_model, api_key=api_key_str)
        LlamaSettings.embed_model = OpenAIEmbedding(api_key=api_key_str)

        if Path(self.persist_dir).exists():
            # Use cached scan
            self._current_index_size = get_rag_dir_size(
                self.persist_dir,
                self.settings.rag_scan_depth_limit,
                DEFAULT_MAX_FILES,
                ttl_hash=int(time.time() // 60),
            )
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
        limit_mb = self.settings.rag_max_index_size_mb
        limit_bytes = calculate_bytes_from_mb(limit_mb)

        if self._current_index_size > limit_bytes:
            msg = ERR_RAG_INDEX_SIZE.format(limit=limit_mb)
            logger.error(msg)
            raise MemoryError(msg)

    def _rate_limit(self) -> None:
        """Simple blocking rate limiter."""
        self._last_call_time = rate_limit(self._last_call_time, self._min_interval)

    def _document_generator(self, request: IngestionRequest) -> Iterator[Document]:
        """
        Yield documents from request content one by one.
        Tracks size updates internally.
        """
        chunk_size = getattr(self.settings, "rag_chunk_size", DEFAULT_RAG_CHUNK_SIZE)
        max_doc_len = getattr(self.settings, "rag_max_document_length", 1_000_000)
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

            if len(content_part) > chunk_size:
                chunks = [
                    content_part[i : i + chunk_size]
                    for i in range(0, len(content_part), chunk_size)
                ]
            else:
                chunks = [content_part]

            for chunk in chunks:
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
        batch_size = getattr(self.settings, "rag_batch_size", DEFAULT_RAG_BATCH_SIZE)

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
            clear_rag_cache()
            self._current_index_size = get_rag_dir_size(
                self.persist_dir,
                self.settings.rag_scan_depth_limit,
                DEFAULT_MAX_FILES,
                ttl_hash=int(time.time() // 60),
            )

    def query(self, question: str) -> str:
        """
        Query the index for relevant context.
        """
        self._rate_limit()

        max_len = self.settings.rag_max_query_length
        question = validate_rag_query(question, max_len, ERR_RAG_QUERY_TOO_LARGE)

        try:
            return self.breaker.call(self._query_impl, question)
        except pybreaker.CircuitBreakerError as e:
            logger.exception("Circuit breaker open.")
            raise NetworkError(ERR_CIRCUIT_OPEN) from e

    def _query_impl(self, question: str) -> str:
        if self.index is None:
            return ERR_RAG_NO_DATA

        if self.settings.rag_rate_limit_interval > 0:
            time.sleep(self.settings.rag_rate_limit_interval)

        timeout = getattr(self.settings, "rag_query_timeout", DEFAULT_RAG_QUERY_TIMEOUT)

        try:
            query_engine = self.index.as_query_engine()

            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(query_engine.query, question)
                response = future.result(timeout=timeout)

            return str(response)

        except FuturesTimeoutError:
            logger.exception("RAG Query timed out after %s seconds", timeout)
            raise RuntimeError(ERR_RAG_QUERY_TIMEOUT) from None
        except Exception as e:
            logger.exception("LlamaIndex query failed: %s", e.__class__.__name__)
            msg = ERR_RAG_QUERY_FAILED.format(error=e)
            raise RuntimeError(msg) from e
