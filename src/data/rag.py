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
        self.persist_dir = persist_dir or self.settings.rag_persist_dir
        self.index: VectorStoreIndex | None = None
        self._init_llama()

    def _init_llama(self) -> None:
        """Initialize LlamaIndex settings and load existing index if available."""
        # Validate keys via settings, but pass them explicitly to classes to avoid os.environ pollution
        if not self.settings.openai_api_key:
             raise ValueError(self.settings.errors.config_missing_openai)

        api_key_str = self.settings.openai_api_key.get_secret_value()

        # Configure global settings for LlamaIndex
        LlamaSettings.llm = OpenAI(
            model=self.settings.llm_model,
            api_key=api_key_str
        )
        LlamaSettings.embedding = OpenAIEmbedding(api_key=api_key_str)  # type: ignore[attr-defined]

        if Path(self.persist_dir).exists():
            try:
                storage_context = StorageContext.from_defaults(persist_dir=self.persist_dir)
                # Helper function type hint is vague in library, casting or ignoring if needed
                self.index = load_index_from_storage(storage_context)  # type: ignore[assignment]
            except Exception:
                logger.warning(f"Failed to load index from {self.persist_dir}, starting fresh.")
                self.index = None

    def ingest_text(self, text: str, source: str) -> None:
        """
        Ingest text into the vector store in-memory.
        Call `persist_index()` explicitly to save to disk.

        Args:
            text: The content to index.
            source: Metadata source (filename, etc).
        """
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
        if self.index is None:
            return "No data available."

        query_engine = self.index.as_query_engine()
        response = query_engine.query(question)
        return str(response)
