from src.core.config import Settings
from src.core.config import Settings
from unittest.mock import MagicMock, patch

import pytest
from langgraph.graph.state import CompiledStateGraph

from src.core.graph import create_app
from src.core.nodes import (
    make_nemawashi_analysis_node,
    make_transcript_ingestion_node,
)
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.politics import InfluenceNetwork, Stakeholder
from src.domain_models.state import GlobalState, Phase
from src.domain_models.transcript import Transcript


@pytest.fixture
def mock_state() -> GlobalState:
    return GlobalState(
        phase=Phase.IDEATION,
        topic="Test Topic",
        selected_idea=LeanCanvas(
            id=1,
            title="Test Idea",
            problem="Problem is big enough.",
            solution="Solution is detailed enough.",
            customer_segments="Segments are defined.",
            unique_value_prop="UVP is unique enough.",
        ),
    )


def test_create_app_structure() -> None:
    """Test that the main application graph is created correctly."""
    from src.core.config import Settings
    from src.core.factory import AgentFactory

    settings = Settings()
    agent_factory = MagicMock(spec=AgentFactory)
    app = create_app(settings=settings, agent_factory=agent_factory)

    assert isinstance(app, CompiledStateGraph)
    # detailed graph structure assertions are hard with compiled graph,
    # but we can check if it compiles without error.


@patch("src.core.nodes.RAG")
def test_transcript_ingestion_node(mock_rag_cls: MagicMock, mock_state: GlobalState) -> None:
    """Test transcript ingestion logic."""
    mock_rag = mock_rag_cls.return_value

    # Setup state with transcripts
    t1 = Transcript(
        source="Interview 1", content="Content 1 is long enough for validation.", date="2023-01-01"
    )
    mock_state.transcripts = [t1]

    from src.core.config import Settings
    settings = Settings()
    transcript_ingestion_node = make_transcript_ingestion_node(settings=settings)
    result = transcript_ingestion_node(mock_state)

    assert result == {}
    mock_rag_cls.assert_called_with(persist_dir=mock_state.rag_index_path)
    mock_rag.ingest_transcript.assert_called_once_with(t1)
    mock_rag.persist_index.assert_called_once()


@patch("src.core.nodes.NemawashiEngine")
def test_nemawashi_analysis_node(mock_engine_cls: MagicMock, mock_state: GlobalState) -> None:
    """Test Nemawashi analysis logic."""
    mock_engine = mock_engine_cls.return_value

    # Setup influence network
    s1 = Stakeholder(name="A", initial_support=0.2, stubbornness=0.1)
    s2 = Stakeholder(name="B", initial_support=0.8, stubbornness=0.1)
    network = InfluenceNetwork(stakeholders=[s1, s2], matrix=[[1.0, 0.0], [0.0, 1.0]])
    mock_state.influence_network = network

    # Mock engine consensus result
    mock_engine.calculate_consensus.return_value = [0.5, 0.5]
    mock_engine.identify_influencers.return_value = ["A"]

    nemawashi_analysis_node = make_nemawashi_analysis_node(mock_engine_cls)
    result = nemawashi_analysis_node(mock_state)

    assert "influence_network" in result
    updated_network = result["influence_network"]
    assert isinstance(updated_network, InfluenceNetwork)
    # Check if support was updated
    assert updated_network.stakeholders[0].initial_support == 0.5
    assert updated_network.stakeholders[1].initial_support == 0.5

    mock_engine.calculate_consensus.assert_called_once()
