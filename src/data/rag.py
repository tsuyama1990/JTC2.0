import logging
import os
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

        LlamaSettings.llm = OpenAI(model=self.settings.llm_model, api_key=api_key_str)
        # Note: LlamaIndex settings typing can be tricky with mypy.
        # We assign directly as recommended in docs, suppressing assignment error if needed.
        LlamaSettings.embed_model = OpenAIEmbedding(api_key=api_key_str)

        # Scalability: Check index size before loading?
        # LlamaIndex local storage is files (docstore.json, index_store.json, etc).
        # We can check file sizes.

        if Path(self.persist_dir).exists():
            # Check if directory is empty
            if not any(Path(self.persist_dir).iterdir()):
                logger.info(f"Persist directory {self.persist_dir} exists but is empty. Initializing new index.")
                self.index = None
                return

            try:
                # Basic OOM protection: Warn if index seems huge (e.g. > 500MB)
                total_size = 0
                # Use os.scandir for better performance on large directories
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

                storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)
                self.index = load_index_from_storage(storage_context)  # type: ignore[assignment]
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

    def ingest_text(self, text: str, source: str) -> None:
        """
        Ingest text into the vector store in-memory.

        Args:
            text: The content to index.
            source: Metadata source.
        """
        # Scalability: Check text length
        if len(text) > 1_000_000:
            logger.warning(
                f"Ingesting large text ({len(text)} chars). Consider chunking before calling ingest."
            )
            # We proceed, but logging helps diagnosis.

        doc = Document(text=text, metadata={"source": source})

        if self.index is None:
            self.index = VectorStoreIndex.from_documents([doc])
        else:
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
        # Security: Sanitize input
        if len(question) > 1000:
            question = question[:1000]

        # Remove potentially dangerous characters if any (e.g. control chars)
        # For RAG, mostly length is the concern for DoS.

        if self.index is None:
            return "No data available."

        query_engine = self.index.as_query_engine()
        response = query_engine.query(question)
        return str(response)
