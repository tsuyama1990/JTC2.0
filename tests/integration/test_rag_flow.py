import contextlib
import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.llms import MockLLM

from src.agents.cpo import CPOAgent
from src.core.config import get_settings
from src.data.rag import RAG
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.state import GlobalState
from tests.conftest import DUMMY_ENV_VARS


class MockEmbedding(BaseEmbedding):
    def _get_query_embedding(self, query: str) -> list[float]:
        return [0.1] * 1536

    def _get_text_embedding(self, text: str) -> list[float]:
        return [0.1] * 1536

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return [0.1] * 1536

    async def _aget_text_embedding(self, text: str) -> list[float]:
        return [0.1] * 1536


@pytest.fixture
def temp_vector_store() -> Generator[str, None, None]:
    """Create a temporary directory for vector store within project root."""
    # RAG enforce stricter path validation (must be relative to CWD)
    base_dir = Path.cwd() / "tests" / "temp_rag_data"
    base_dir.mkdir(parents=True, exist_ok=True)
    try:
        temp_dir = tempfile.mkdtemp(dir=str(base_dir))
        yield temp_dir
    finally:
        # Cleanup
        if 'temp_dir' in locals() and Path(temp_dir).exists():
            shutil.rmtree(temp_dir)

        # Try to remove the base dir if empty to keep project clean
        with contextlib.suppress(OSError):
            base_dir.rmdir()


@patch.dict("os.environ", DUMMY_ENV_VARS)
def test_rag_integration_flow(temp_vector_store: str) -> None:
    """
    Integration test for RAG: Ingest -> Persist -> Query.
    Uses real LlamaIndex components with MockLLM/MockEmbedding to simulate logic without API calls.
    """
    get_settings.cache_clear()

    # We patch the models at the point of instantiation inside RAG
    # This allows RAG to build a real index structure, but using deterministic, fake embeddings
    with (
        patch("src.data.rag.OpenAI", return_value=MockLLM()),
        patch("src.data.rag.OpenAIEmbedding", return_value=MockEmbedding(embed_dim=1536)),
    ):
        # Initialize RAG with temp path
        rag = RAG(persist_dir=temp_vector_store)

        # 1. Ingest
        # We ingest specific text. The MockEmbedding returns constant vectors [0.1]*1536
        # So essentially all text is identical in vector space, but the retrieval logic runs.
        text = "Customers prefer subscription models."
        rag.ingest_text(text, source="test_interview.txt")

        # 2. Persist
        rag.persist_index()

        # Verify files created
        from pathlib import Path
        assert any(Path(temp_vector_store).iterdir())

        # 3. Reload (simulate new instance)
        rag_loaded = RAG(persist_dir=temp_vector_store)
        assert rag_loaded.index is not None

        # 4. Query
        # Instead of mocking `as_query_engine`, we let it run.
        # Since MockLLM is used, it will return a mock response, but the RETRIEVAL step happens.
        # Because we use constant embeddings, the retrieval should find the document we just added
        # (it's the only one and matches perfectly).

        answer = rag_loaded.query("What do customers prefer?")

        # LlamaIndex MockLLM by default echoes the prompt or a standard response.
        # We just want to ensure it didn't crash and returned a string.
        assert isinstance(answer, str)
        assert len(answer) > 0


@patch.dict("os.environ", DUMMY_ENV_VARS)
def test_cpo_agent_behavior() -> None:
    """Test CPO Agent behavior with mocked RAG."""
    get_settings.cache_clear()
    llm = MagicMock()
    # Mock chain invoke
    mock_msg = MagicMock()
    mock_msg.content = "Pivot now."
    llm.invoke.return_value = mock_msg
    llm.return_value = mock_msg

    # Init agent with valid path to pass strict validation
    # This path is relative to CWD and starts with 'tests'
    agent = CPOAgent(llm, rag_path="tests/mock_cpo_rag")

    # Mock internal RAG
    agent.rag = MagicMock()
    agent.rag.query.return_value = "Evidence found."

    # State
    state = GlobalState(
        topic="Test",
        selected_idea=LeanCanvas(
            id=1,
            title="Test Idea Title",
            problem="Problem statement description",
            solution="Solution description text",
            customer_segments="Customer Segments List",
            unique_value_prop="Unique Value Proposition Text",
        ),
    )

    # Run
    res = agent.run(state)

    # Check RAG usage
    agent.rag.query.assert_called()
    # Check output
    assert res["debate_history"][-1].content == "Pivot now."
