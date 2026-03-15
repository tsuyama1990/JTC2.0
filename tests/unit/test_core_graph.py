from unittest.mock import MagicMock, patch

import pytest
from langgraph.graph.state import CompiledStateGraph

from src.core.graph import create_app
from src.core.nodes import (
    final_artifact_generation_node,
    nemawashi_analysis_node,
    solution_proposal_node,
    transcript_ingestion_node,
)
from src.domain_models.agent_spec import AgentPromptSpec, StateMachine
from src.domain_models.experiment import ExperimentPlan, MetricTarget
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.metrics import Financials, RingiSho
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

    # Extract underlying builder graph structure
    graph = app.builder

    # Assert all expected nodes exist
    expected_nodes = [
        "ideator",
        "verification",
        "transcript_ingestion",
        "simulation_round",
        "nemawashi_analysis",
        "cpo_mentoring",
        "solution_proposal",
        "spec_generation",
        "experiment_planning",
        "pmf",
        "governance",
        "final_artifact_generation",
    ]
    for node in expected_nodes:
        assert node in graph.nodes, f"Node {node} missing from graph"

    # Check key edge configurations via the builder's edges list
    edges = list(graph.edges)
    assert any(e[0] == "governance" and e[1] == "final_artifact_generation" for e in edges), (
        "Missing edge: governance -> final_artifact_generation"
    )


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


@patch("src.core.services.file_service.FileService")
@patch("fpdf.FPDF")
@patch("os.makedirs")
def test_final_artifact_generation_node(
    mock_makedirs: MagicMock,
    mock_fpdf_cls: MagicMock,
    mock_fs_cls: MagicMock,
    mock_state: GlobalState,
) -> None:
    """Test the generation of final artifacts (Markdown and PDF)."""
    mock_fs = mock_fs_cls.return_value

    story = UserStory(
        as_a="User",
        i_want_to="do something",
        so_that="I get value",
        acceptance_criteria=["Criterion 1"],
        target_route="/home",
    )
    # Add dummy spec and experiment to state
    mock_state.agent_prompt_spec = AgentPromptSpec(
        sitemap="Test Sitemap",
        routing_and_constraints="Test Constraints",
        core_user_story=story,
        state_machine=StateMachine(
            success="Success State",
            loading="Loading State",
            error="Error State",
            empty="Empty State",
        ),
        validation_rules="Validation rules here",
        mermaid_flowchart="graph TD;",
    )
    mock_state.experiment_plan = ExperimentPlan(
        riskiest_assumption="Test assumption",
        experiment_type="LP",
        acquisition_channel="Ads",
        aarrr_metrics=[
            MetricTarget(metric_name="Metric 1", target_value="10%", measurement_method="Logs")
        ],
        pivot_condition="If failure happens",
    )
    mock_state.ringi_sho = RingiSho(
        title="Test Proposal",
        executive_summary="Summary is long enough for the check.",
        financial_projection=Financials(cac=10, ltv=100, payback_months=1, roi=10),
        risks=["Risk 1"],
        approval_status="Approved",
    )

    result = final_artifact_generation_node(mock_state)

    # Verify it completes without error
    assert result == {}

    # Verify FileService is used to write Markdown files
    assert mock_fs.save_text_async.call_count == 3
    # Check that it attempted to write AgentPromptSpec, ExperimentPlan, and RingiSho
    call_args = [call[0][1] for call in mock_fs.save_text_async.call_args_list]
    assert any("AgentPromptSpec.md" in str(arg) for arg in call_args)
    assert any("ExperimentPlan.md" in str(arg) for arg in call_args)
    assert any("RingiSho.md" in str(arg) for arg in call_args)

    # Verify PDF generation logic is called via FileService using async method
    mock_fs.save_pdf_async.assert_called_once()
    assert "outputs" in str(mock_fs.save_pdf_async.call_args[0][1])

    # Verify that we wait on the future result
    mock_fs.save_pdf_async.return_value.result.assert_called_once()
