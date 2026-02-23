import logging
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
        # Simple check: restrict to current directory or strict subdirs
        # For this context, we allow relative paths but ensure no traversing up
        if ".." in path_str:
             msg = "Path traversal detected in persist_dir"
             raise ValueError(msg)
        return path_str

    def _init_llama(self) -> None:
        """Initialize LlamaIndex settings and load existing index if available."""
        if not self.settings.openai_api_key:
             raise ValueError(self.settings.errors.config_missing_openai)

        api_key_str = self.settings.openai_api_key.get_secret_value()

        LlamaSettings.llm = OpenAI(
            model=self.settings.llm_model,
            api_key=api_key_str
        )
        LlamaSettings.embed_model = OpenAIEmbedding(api_key=api_key_str)  # type: ignore[attr-defined]

        # Scalability: Check index size before loading?
        # LlamaIndex local storage is files (docstore.json, index_store.json, etc).
        # We can check file sizes.

        if Path(self.persist_dir).exists():
            try:
                # Basic OOM protection: Warn if index seems huge (e.g. > 500MB)
                # This is heuristic.
                total_size = sum(f.stat().st_size for f in Path(self.persist_dir).glob("**/*") if f.is_file())
                if total_size > 500 * 1024 * 1024:
                    logger.warning(f"Vector store at {self.persist_dir} is large ({total_size/1024/1024:.1f} MB). Loading may impact memory.")

                storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)
                self.index = load_index_from_storage(storage_context)  # type: ignore[assignment]
            except Exception:
                logger.warning(f"Failed to load index from {self.persist_dir}, starting fresh.")
                self.index = None

    def ingest_text(self, text: str, source: str) -> None:
        """
        Ingest text into the vector store in-memory.

        Args:
            text: The content to index.
            source: Metadata source.
        """
        # Scalability: Check text length
        if len(text) > 1_000_000:
            logger.warning(f"Ingesting large text ({len(text)} chars). Consider chunking before calling ingest.")
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
