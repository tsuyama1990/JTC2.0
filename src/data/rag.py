import logging
import os
import sys
from pathlib import Path

from llama_index.core import Document, VectorStoreIndex, load_index_from_storage
from llama_index.core import Settings as LlamaSettings
from llama_index.core.storage.storage_context import StorageContext
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

from src.core.config import get_settings

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

        self.index: VectorStoreIndex | None = None
        self._init_llama()

    def _validate_path(self, path_str: str) -> str:
        """Ensure persist directory is safe and absolute."""
        try:
            # Use strict=True (available in recent Python versions for resolve)
            # if the path exists, otherwise False.
            # We want to allow creating new paths, but they must be within root.
            # Using resolve() handles symlinks.
            path = Path(path_str).resolve()
        except Exception as e:
            msg = f"Invalid path: {e}"
            raise ValueError(msg) from e

        cwd = Path.cwd().resolve()

        # Strict allowlist check: Must be relative to CWD (Project Root)
        if not path.is_relative_to(cwd):
            msg = "Path traversal detected in persist_dir. Must be within project root."
            raise ValueError(msg)
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
            logger.info(f"Persist directory {self.persist_dir} exists but is empty. Initializing new index.")
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
            # Standardized Error
            raise RuntimeError(f"RAG Index Load Error: {e}") from e

    def _check_index_size(self) -> None:
        """
        Check if the index is too large and raise error if unsafe.
        Uses rglob for cleaner recursion.
        """
        total_size = 0
        limit_mb = self.settings.rag_max_index_size_mb
        limit_bytes = limit_mb * 1024 * 1024

        try:
            # Efficiently sum file sizes
            total_size = sum(f.stat().st_size for f in Path(self.persist_dir).rglob('*') if f.is_file())
        except OSError as e:
            logger.warning(f"Error scanning index directory: {e}")
            # Fail safe or proceed? Proceeding might be risky if we can't read.
            # But let's warn.

        if total_size > limit_bytes:
            msg = f"Vector store size ({total_size / 1024 / 1024:.2f} MB) exceeds limit ({limit_mb} MB). Loading blocked for memory safety."
            logger.error(msg)
            raise MemoryError(msg)

    def ingest_text(self, text: str, source: str) -> None:
        """
        Ingest text into the vector store in-memory.
        """
        chunk_size = self.settings.rag_chunk_size

        if len(text) > chunk_size:
            logger.info(f"Text too large ({len(text)} chars). Chunking...")
            chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
        else:
            chunks = [text]

        documents = [Document(text=chunk, metadata={"source": source, "chunk_index": i}) for i, chunk in enumerate(chunks)]

        try:
            if self.index is None:
                self.index = VectorStoreIndex.from_documents(documents)
            else:
                for doc in documents:
                    self.index.insert(doc)
        except Exception as e:
            logger.error(f"Failed to ingest document from {source}: {e}")
            # Decide whether to raise or suppress.
            # Suppressing ensures partial success in batch ops, but usually we want to know.
            # Let's raise to be explicit.
            raise RuntimeError(f"Ingestion failed: {e}") from e

    def persist_index(self) -> None:
        """Persist the index to disk."""
        if self.index:
            self.index.storage_context.persist(persist_dir=self.persist_dir)
            logger.info(f"Index persisted to {self.persist_dir}")

    def query(self, question: str) -> str:
        """
        Query the index for relevant context.
        """
        # Data Integrity: Strict Type Check
        if not isinstance(question, str):
             raise ValueError("Query must be a string.")

        if not question.strip():
             raise ValueError("Query cannot be empty.")

        max_len = self.settings.rag_max_query_length
        if len(question) > max_len:
            logger.warning(f"Query too long ({len(question)} chars). Truncating to {max_len}.")
            question = question[:max_len]

        # Sanitization
        question = question.strip()

        if self.index is None:
            return "No data available."

        query_engine = self.index.as_query_engine()
        response = query_engine.query(question)
        return str(response)
