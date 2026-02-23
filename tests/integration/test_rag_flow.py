import shutil
import tempfile
from collections.abc import Generator
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
    """Create a temporary directory for vector store."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@patch.dict("os.environ", DUMMY_ENV_VARS)
def test_rag_integration_flow(temp_vector_store: str) -> None:
    """
    Integration test for RAG: Ingest -> Persist -> Query.
    Uses real LlamaIndex components (mocked LLM/Embeddings to avoid API calls).
    """
    get_settings.cache_clear()
    # Mocking secret value getter for Pydantic SecretStr (via cached settings is hard,
    # but DUMMY_ENV_VARS ensures keys exist)

    # We mock OpenAI and OpenAIEmbedding to avoid real API calls.
    # We patch them where they are used in src.data.rag to ensure RAG uses the mocks
    # even if already imported.
    with patch("src.data.rag.OpenAI", return_value=MockLLM()), \
         patch("src.data.rag.OpenAIEmbedding", return_value=MockEmbedding(embed_dim=1536)):

        # Initialize RAG with temp path
        rag = RAG(persist_dir=temp_vector_store)

        # 1. Ingest
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

        # 4. Query (Mock the query engine response since we don't have real embeddings)
        # Real query would fail with fake embeddings matching nothing or erroring on mock.
        # But we verified index loading.

        # We can mock the query engine on the loaded instance to verify connection
        with patch.object(rag_loaded.index, "as_query_engine") as mock_engine:
            mock_response = MagicMock()
            # Explicit assignment for return value of str()
            mock_response.__str__ = MagicMock(return_value="Verified answer.")  # type: ignore[method-assign]
            mock_engine.return_value.query.return_value = mock_response

            answer = rag_loaded.query("What do customers prefer?")
            assert answer == "Verified answer."

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

    # Init agent
    agent = CPOAgent(llm, rag_path="./dummy")

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
            unique_value_prop="Unique Value Proposition Text"
        )
    )

    # Run
    res = agent.run(state)

    # Check RAG usage
    agent.rag.query.assert_called()
    # Check output
    assert res["debate_history"][-1].content == "Pivot now."
