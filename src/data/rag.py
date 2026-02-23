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
        """Ensure persist directory is safe."""
        # Use strict resolution to catch symlinks
        try:
            path = Path(path_str).resolve(strict=False)
        except Exception as e:
            msg = f"Invalid path: {e}"
            raise ValueError(msg) from e

        cwd = Path.cwd().resolve()

        # Strict allowlist check: Must be relative to CWD
        if not path.is_relative_to(cwd):
            msg = "Path traversal detected in persist_dir. Must be within project root."
            raise ValueError(msg)
        return str(path)

    def _init_llama(self) -> None:
        """Initialize LlamaIndex settings and load existing index if available."""
        if not self.settings.openai_api_key:
            raise ValueError(self.settings.errors.config_missing_openai)

        api_key_str = self.settings.openai_api_key.get_secret_value()

        # Use settings for model names to avoid hardcoding
        LlamaSettings.llm = OpenAI(model=self.settings.llm_model, api_key=api_key_str)
        # Assuming embedding model can also be configured or defaults safely.
        # For now, we use the standard OpenAI embedding but ensure key is passed.
        LlamaSettings.embed_model = OpenAIEmbedding(api_key=api_key_str)

        if Path(self.persist_dir).exists():
            self._load_existing_index()

    def _load_existing_index(self) -> None:
        """Load the index from storage if it exists and is valid."""
        # Check if directory is empty
        if not any(Path(self.persist_dir).iterdir()):
            logger.info(f"Persist directory {self.persist_dir} exists but is empty. Initializing new index.")
            self.index = None
            return

        try:
            self._check_index_size()
            storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)

            # Memory Monitoring
            logger.info(f"Loading index from {self.persist_dir}...")
            self.index = load_index_from_storage(storage_context)  # type: ignore[assignment]

            # Rough memory check (shallow)
            size_mb = sys.getsizeof(self.index) / (1024 * 1024)
            logger.debug(f"Loaded index object size (shallow): {size_mb:.2f} MB")

        except Exception as e:
            logger.exception("Failed to load index from %s", self.persist_dir)
            self.index = None
            # User notification via exception message
            msg = (
                f"CRITICAL: Failed to load RAG index from '{self.persist_dir}'. "
                "The index may be corrupted or incompatible. "
                "Please check the logs or try re-ingesting data."
            )
            raise RuntimeError(msg) from e

    def _check_index_size(self) -> None:
        """Check if the index is too large and warn."""
        total_size = 0
        stack = [self.persist_dir]
        while stack:
            current_dir = stack.pop()
            try:
                with os.scandir(current_dir) as it:
                    for entry in it:
                        if entry.is_file():
                            total_size += entry.stat().st_size
                        elif entry.is_dir():
                            stack.append(entry.path)
            except PermissionError:
                logger.warning(f"Permission denied scanning {current_dir}")

        if total_size > 500 * 1024 * 1024:
            logger.warning(
                f"Vector store at {self.persist_dir} is large ({total_size / 1024 / 1024:.1f} MB). Loading may impact memory."
            )

    def ingest_text(self, text: str, source: str) -> None:
        """
        Ingest text into the vector store in-memory.

        Chunking logic implemented to handle large inputs.
        """
        # Scalability: Chunk text if too large
        chunk_size = 4000  # Reasonable chunk size for embeddings
        if len(text) > chunk_size:
            logger.info(f"Text too large ({len(text)} chars). Chunking...")
            chunks = [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]
        else:
            chunks = [text]

        documents = [Document(text=chunk, metadata={"source": source, "chunk_index": i}) for i, chunk in enumerate(chunks)]

        if self.index is None:
            self.index = VectorStoreIndex.from_documents(documents)
        else:
            for doc in documents:
                self.index.insert(doc)

    def persist_index(self) -> None:
        """Persist the index to disk."""
        if self.index:
            self.index.storage_context.persist(persist_dir=self.persist_dir)
            logger.info(f"Index persisted to {self.persist_dir}")

    def query(self, question: str) -> str:
        """
        Query the index for relevant context.
        """
        # Security: Sanitize input & Length validation
        if not question or not isinstance(question, str):
             return "Invalid query."

        if len(question) > 500:
            logger.warning("Query too long. Truncating.")
            question = question[:500]

        # Basic sanitization (remove potential control chars if needed, though mostly handled by LLM lib)
        question = question.strip()

        if self.index is None:
            return "No data available."

        query_engine = self.index.as_query_engine()
        response = query_engine.query(question)
        return str(response)
