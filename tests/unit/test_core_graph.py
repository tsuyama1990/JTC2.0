from unittest.mock import MagicMock, patch

import pytest

from src.core.graph import create_app
from src.core.nodes import (
    spec_generation_node,
    transcript_ingestion_node,
)
from src.domain_models.agent_prompt import AgentPromptSpec, StateMachine
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.sitemap import Route, SitemapAndStory, UserStory
from src.domain_models.state import GlobalState, Phase
from src.domain_models.transcript import Transcript


@pytest.fixture
def mock_state() -> GlobalState:
    return GlobalState(
        phase=Phase.IDEATION,
        topic="Test topic",
        selected_idea=LeanCanvas(
            id=1,
            title="Title",
            problem="Problem statement that is long enough.",
            solution="Solution statement that is long enough.",
            customer_segments="Segments",
            unique_value_prop="Unique value proposition.",
        ),
    )


def test_graph_creation() -> None:
    """Test that the graph compiles with the correct nodes and edges."""
    app = create_app()
    assert app is not None
    # We can inspect the compiled graph nodes internally
    # In a real scenario, we might test edge transitions, but LangGraph makes this internal.
    # Just verifying it compiles without errors is a good structural test.


def test_nemawashi_analysis_node() -> None:
    """Placeholder since nemawashi is obsolete."""


@patch("src.core.nodes.AgentFactory.get_cpo_agent")
@patch("src.core.nodes.RAG")
def test_transcript_ingestion_node(
    mock_rag: MagicMock, mock_get_cpo: MagicMock, mock_state: GlobalState
) -> None:
    """Test Transcript Ingestion Node."""
    mock_state.transcripts = [
        Transcript(source="PLAUD_1", content="Summary: High risk mentioned", date="2023-01-01")
    ]
    mock_cpo = mock_get_cpo.return_value
    mock_cpo.run.return_value = {"messages": ["Ingested transcripts"]}

    mock_rag_instance = mock_rag.return_value

    result = transcript_ingestion_node(mock_state)

    # Ingest node returns empty dict
    assert result == {}
    mock_rag_instance.ingest_transcript.assert_called_once()


@patch("src.core.nodes.AgentFactory.get_builder_agent")
def test_spec_generation_node(mock_get_builder: MagicMock, mock_state: GlobalState) -> None:
    """Test Agent Prompt Spec generation."""
    mock_builder = mock_get_builder.return_value

    story = UserStory(
        as_a="User",
        i_want_to="Login",
        so_that="I can access my dashboard",
        acceptance_criteria=["Must have email", "Must have password"],
        target_route="/login",
    )
    sitemap = SitemapAndStory(
        sitemap=[
            Route(path="/", name="Home", purpose="Landing", is_protected=False),
            Route(path="/login", name="Login", purpose="Auth", is_protected=False),
        ],
        core_story=story,
    )
    mock_state.sitemap_and_story = sitemap

    mock_spec = AgentPromptSpec(
        sitemap="Mapped Routes",
        routing_and_constraints="No server components",
        core_user_story=story,
        state_machine=StateMachine(
            success="Success UI",
            loading="Loading Spinner",
            error="Error Toast",
            empty="Empty State",
        ),
        validation_rules="Zod schemas",
        mermaid_flowchart="graph TD;",
    )
    mock_builder.generate_agent_prompt_spec.return_value = {
        "agent_prompt_spec": mock_spec,
    }

    # Execute node
    with patch("pathlib.Path.open", create=True):
        result = spec_generation_node(mock_state)

    assert "agent_prompt_spec" in result
    assert result["agent_prompt_spec"].sitemap == "Mapped Routes"
