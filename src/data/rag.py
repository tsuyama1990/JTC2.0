import logging
import os
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
    ERR_RAG_TEXT_TOO_LARGE,
)

logger = logging.getLogger(__name__)


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

        self.index: VectorStoreIndex | None = None
        self._init_llama()

    def _validate_path(self, path_str: str) -> str:
        """Ensure persist directory is safe and absolute."""
        try:
            path = Path(path_str).resolve()
        except Exception as e:
            msg = f"Invalid path: {e}"
            raise ValueError(msg) from e

        cwd = Path.cwd().resolve()

        # Strict allowlist check: Must be relative to CWD
        if not path.is_relative_to(cwd):
            raise ValueError(ERR_PATH_TRAVERSAL)
        return str(path)

    def _init_llama(self) -> None:
        """Initialize LlamaIndex settings and load existing index if available."""
        if not self.settings.openai_api_key:
            raise ValueError(self.settings.errors.config_missing_openai)

        api_key_str = self.settings.openai_api_key.get_secret_value()

        LlamaSettings.llm = OpenAI(model=self.settings.llm_model, api_key=api_key_str)
        LlamaSettings.embed_model = OpenAIEmbedding(api_key=api_key_str)

        if Path(self.persist_dir).exists():
            self._load_existing_index()

    def _load_existing_index(self) -> None:
        """Load the index from storage if it exists and is valid."""
        if not any(Path(self.persist_dir).iterdir()):
            logger.info(
                f"Persist directory {self.persist_dir} exists but is empty. Initializing new index."
            )
            self.index = None
            return

        try:
            self._check_index_size()
            storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)

            logger.info(f"Loading index from {self.persist_dir}...")
            self.index = load_index_from_storage(storage_context)  # type: ignore[assignment]

        except Exception as e:
            logger.exception("Failed to load index from %s", self.persist_dir)
            self.index = None
            msg = f"RAG Index Load Error: {e}"
            raise RuntimeError(msg) from e

    def _check_index_size(self) -> None:
        """
        Check if the index is too large and raise error if unsafe.
        Uses optimized scanning with early termination.
        """
        limit_mb = self.settings.rag_max_index_size_mb
        limit_bytes = limit_mb * 1024 * 1024

        size = self._get_dir_size(self.persist_dir, limit_bytes)
        if size > limit_bytes:
            msg = ERR_RAG_INDEX_SIZE.format(limit=limit_mb)
            logger.error(msg)
            raise MemoryError(msg)

    def _get_dir_size(self, path: str, limit: int) -> int:
        """Recursive directory size calculation with early exit."""
        total = 0
        try:
            with os.scandir(path) as it:
                for entry in it:
                    if entry.is_file():
                        total += entry.stat().st_size
                    elif entry.is_dir():
                        total += self._get_dir_size(entry.path, limit - total)

                    if total > limit:
                        return total
        except OSError as e:
            logger.warning(f"Error scanning index directory: {e}")
        return total

    def ingest_text(self, text: str, source: str) -> None:
        """
        Ingest text into the vector store in-memory.
        Uses batch insertion.
        """
        # Audit Fix: Validation
        max_len = self.settings.rag_max_document_length
        if len(text) > max_len:
            msg = ERR_RAG_TEXT_TOO_LARGE.format(size=len(text))
            raise ValueError(msg)

        chunk_size = self.settings.rag_chunk_size

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
        if not isinstance(question, str):
            msg = "Query must be a string."
            raise TypeError(msg)

        if not question.strip():
            msg = "Query cannot be empty."
            raise ValueError(msg)

        max_len = self.settings.rag_max_query_length
        if len(question) > max_len:
            logger.warning(f"Query too long ({len(question)} chars). Truncating to {max_len}.")
            question = question[:max_len]

        question = question.strip()

        try:
            return self.breaker.call(self._query_impl, question)
        except pybreaker.CircuitBreakerError:
            logger.exception("Circuit breaker open.")
            return ERR_CIRCUIT_OPEN

    def _query_impl(self, question: str) -> str:
        if self.index is None:
            return "No data available."

        query_engine = self.index.as_query_engine()
        response = query_engine.query(question)
        return str(response)
