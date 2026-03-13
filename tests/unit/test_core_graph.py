from unittest.mock import MagicMock, patch

import pytest
from langgraph.graph.state import CompiledStateGraph

from src.core.graph import create_app
from src.core.nodes import (
    governance_node,
    mvp_generation_node,
    nemawashi_analysis_node,
    solution_proposal_node,
    transcript_ingestion_node,
)
from src.domain_models.agent_spec import AgentPromptSpec, StateMachine
from src.domain_models.experiment import ExperimentPlan, MetricTarget
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.mvp import MVPSpec
from src.domain_models.persona import Persona
from src.domain_models.politics import InfluenceNetwork, Stakeholder
from src.domain_models.sitemap import UserStory
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
    app = create_app()
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

    result = nemawashi_analysis_node(mock_state)

    assert "influence_network" in result
    updated_network = result["influence_network"]
    assert isinstance(updated_network, InfluenceNetwork)
    # Check if support was updated
    assert updated_network.stakeholders[0].initial_support == 0.5
    assert updated_network.stakeholders[1].initial_support == 0.5

    mock_engine.calculate_consensus.assert_called_once()


@patch("src.core.nodes.AgentFactory.get_builder_agent")
def test_solution_proposal_node(mock_get_builder: MagicMock, mock_state: GlobalState) -> None:
    """Test solution proposal (feature extraction)."""
    # Setup requirements
    mock_state.target_persona = MagicMock(spec=Persona)  # Required for validation

    mock_builder = mock_get_builder.return_value
    mock_builder.propose_features.return_value = {"candidate_features": ["F1", "F2"]}

    result = solution_proposal_node(mock_state)

    # Note: solution_proposal_node now returns result of _solution_proposal_impl which sets phase
    assert result["phase"] == Phase.SOLUTION
    assert result["candidate_features"] == ["F1", "F2"]


@patch("src.core.nodes.AgentFactory.get_builder_agent")
def test_mvp_generation_node(mock_get_builder: MagicMock, mock_state: GlobalState) -> None:
    """Test MVP generation."""
    mock_builder = mock_get_builder.return_value

    spec = MVPSpec(app_name="App", core_feature="Feature is long enough", v0_prompt="Prompt")
    mock_builder.generate_mvp.return_value = {
        "mvp_spec": spec,
        "mvp_url": "https://v0.dev/123",
        "selected_feature": "Feature is long enough",
    }

    result = mvp_generation_node(mock_state)

    assert "mvp_definition" in result
    assert str(result["mvp_definition"].v0_url).rstrip("/") == "https://v0.dev/123"
    assert result["mvp_definition"].core_features[0].name == "Feature is long enough"


@patch("src.core.nodes.FileService")
@patch("src.core.nodes.get_settings")
@patch("src.core.nodes.AgentFactory.get_governance_agent")
def test_governance_node_saves_artifacts(
    mock_get_gov: MagicMock,
    mock_get_settings: MagicMock,
    mock_fs_class: MagicMock,
    mock_state: GlobalState,
) -> None:
    """Test governance node saving artifacts."""
    mock_gov = mock_get_gov.return_value
    mock_gov.run.return_value = {"ringi_sho": MagicMock()}

    mock_fs = mock_fs_class.return_value

    # We only set experiment_plan, we need to assert based on what is available

    mock_state.agent_prompt_spec = AgentPromptSpec(
        sitemap="Sitemap description here.",
        routing_and_constraints="SSR constraints here.",
        core_user_story=UserStory(
            as_a="User",
            i_want_to="Action",
            so_that="Value",
            acceptance_criteria=["Criteria"],
            target_route="/home",
        ),
        state_machine=StateMachine(
            success="Success", loading="Loading", error="Error", empty="Empty"
        ),
        validation_rules="Rules here",
        mermaid_flowchart="Flowchart here",
    )

    mock_state.experiment_plan = ExperimentPlan(
        riskiest_assumption="Assumption",
        experiment_type="Type",
        acquisition_channel="Channel",
        aarrr_metrics=[
            MetricTarget(metric_name="Metric", target_value="Value", measurement_method="Method")
        ],
        pivot_condition="Condition",
    )

    result = governance_node(mock_state)
    assert result["phase"] == Phase.GOVERNANCE
    assert mock_fs.save_text_sync.call_count == 2

    assert mock_fs.save_pdf_sync.call_count == 1
