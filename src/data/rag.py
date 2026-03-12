import logging
import os
import time
from collections.abc import Iterator
from pathlib import Path

import pybreaker
from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.core.config import get_settings
from src.core.constants import (
    ERR_CIRCUIT_OPEN,
    ERR_RAG_QUERY_TOO_LARGE,
)
from src.core.exceptions import ConfigurationError, NetworkError, ValidationError
from src.core.execution import execute_query_with_timeout
from src.core.interfaces import IVectorStore
from src.core.rate_limit import rate_limit_wait
from src.core.security import sanitize_query, validate_safe_path
from src.core.text_processing import chunk_text_generator
from src.core.utils import scan_directory_size_cached
from src.core.validation import validate_index_size
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
            self._current_index_size = scan_directory_size_cached(
                self.persist_dir,
                depth_limit=self.settings.rag_scan_depth_limit,
                ttl_hash=int(time.time() // 60),  # Refresh every minute
            )

        self.index: IVectorStore | None = None
        self._init_llama()

    def _validate_path(self, path_str: str) -> str:
        """Ensure persist directory is safe."""
        return validate_safe_path(path_str, self.settings.rag_allowed_paths)

    def _init_llama(self) -> None:
        """Initialize LlamaIndex settings and load existing index if available."""
        import os

        is_mock = os.getenv("MOCK_MODE", "false").lower() == "true"

        if not is_mock:
            if not self.settings.openai_api_key:
                raise ConfigurationError(self.settings.errors.config_missing_openai)

            api_key_str = self.settings.openai_api_key.get_secret_value()

            # Local import to prevent architectural hard-coupling at module level
            from llama_index.core import Settings as LlamaSettings
            from llama_index.embeddings.openai import OpenAIEmbedding
            from llama_index.llms.openai import OpenAI

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
            from llama_index.core import load_index_from_storage
            from llama_index.core.storage.storage_context import StorageContext

            storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)
            logger.info(f"Loading index from {self.persist_dir}...")
            self.index = load_index_from_storage(storage_context)

        except Exception:
            logger.exception("Failed to load index from %s", self.persist_dir)
            self.index = None

    def _check_index_size_limit(self) -> None:
        """Check if the tracked index size is too large."""
        validate_index_size(self._current_index_size, self.settings.rag_max_index_size_mb)

    def _rate_limit(self) -> None:
        """Simple blocking rate limiter."""
        self._last_call_time = rate_limit_wait(self._last_call_time, self._min_interval)

    def _size_tracker_callback(self, size_bytes: int) -> None:
        """Callback to update and check size."""
        self._current_index_size += size_bytes
        self._check_index_size_limit()

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

        doc_iterator = chunk_text_generator(
            request.text,
            request.source,
            self.settings.rag_chunk_size,
            self.settings.rag_max_document_length,
            self._size_tracker_callback,
        )
        batch_size = self.settings.rag_batch_size

        # Generator that yields batches of documents
        from llama_index.core import Document

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
                from llama_index.core import VectorStoreIndex

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
            # Using getattr to avoid tight coupling error
            storage_context = getattr(self.index, "storage_context", None)
            if storage_context:
                storage_context.persist(persist_dir=self.persist_dir)
                logger.info(f"Index persisted to {self.persist_dir}")
            scan_directory_size_cached.cache_clear()
            self._current_index_size = scan_directory_size_cached(
                self.persist_dir,
                self.settings.rag_scan_depth_limit,
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

        question = sanitize_query(question)

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

        timeout = getattr(self.settings, "rag_query_timeout", 30.0)

        return execute_query_with_timeout(
            self.index.as_query_engine(), question, timeout, self.settings.rag_rate_limit_interval
        )
