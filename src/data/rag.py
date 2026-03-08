from collections.abc import Iterator

from src.adapters.rag_adapter import LlamaIndexRAGAdapter
from src.core.interfaces import RAGInterface
from src.domain_models.transcript import Transcript


class RAG(RAGInterface):
    """
    Orchestrator for Retrieval-Augmented Generation (RAG).
    Delegates to the LlamaIndex adapter.
    """

    def __init__(self, persist_dir: str | None = None) -> None:
        self.adapter = LlamaIndexRAGAdapter(persist_dir=persist_dir)

    def ingest_text(self, text: str | Iterator[str], source: str) -> None:
        self.adapter.ingest_text(text, source)

    def query(self, question: str) -> str:
        return self.adapter.query(question)

    def persist_index(self) -> None:
        self.adapter.persist_index()

    def ingest_transcript(self, transcript: Transcript) -> None:
        self.adapter.ingest_transcript(transcript)
