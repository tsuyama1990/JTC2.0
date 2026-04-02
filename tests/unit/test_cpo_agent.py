from unittest.mock import MagicMock, patch

import pytest

from src.agents.cpo import CPOAgent
from src.core.config import get_settings
from src.domain_models.alternative import AlternativeAnalysis, AlternativeTool
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.politics import DenseInfluenceNetwork, Stakeholder
from src.domain_models.simulation import DialogueMessage, Role
from src.domain_models.state import GlobalState
from src.domain_models.value_proposition import CustomerProfile, ValueMap, ValuePropositionCanvas


def test_cpo_agent_initialization_invalid_path() -> None:
    """Test CPO Agent path traversal rejection."""
    get_settings.cache_clear()

    mock_llm = MagicMock()
    # Try to initialize with a forbidden path
    with pytest.raises(ValueError, match="Invalid RAG path"):
        CPOAgent(
            llm=mock_llm,
            search_tool=MagicMock(),
            app_settings=get_settings(),
            rag_path="../../../etc/passwd",
        )


def test_cpo_agent_run_no_transcripts() -> None:
    """Test CPO agent run handles missing transcripts properly."""
    get_settings.cache_clear()

    # Mock LLM and RAG
    mock_llm = MagicMock()
    mock_chain_result = MagicMock()
    mock_chain_result.content = "Generic advice."
    mock_llm.invoke.return_value = mock_chain_result
    mock_llm.return_value = mock_chain_result

    # The actual RAG query mock
    with patch("src.agents.cpo.RAG") as MockRAG:
        mock_rag_instance = MockRAG.return_value
        mock_rag_instance.query.return_value = "No transcripts found context."

        agent = CPOAgent(
            llm=mock_llm,
            search_tool=MagicMock(),
            app_settings=get_settings(),
            rag_path="tests/temp_rag",
        )

        state = GlobalState(
            topic="Idea",
            transcripts=[],  # empty
            selected_idea=LeanCanvas(
                id=1,
                title="Generic Title",
                problem="Problem that has three words",
                solution="Solution that has three words",
                customer_segments="C",
                unique_value_prop="Unique value that has three words",
            ),
        )

        res = agent.run(state)

        # For our tests to work reliably we shouldn't rely on isinstance MagicMock skipping
        last_msg = res["debate_history"][-1]
        assert isinstance(last_msg, DialogueMessage)
        assert last_msg.role == Role.CPO

        # Should call query with "against general knowledge"
        mock_rag_instance.query.assert_called_with(
            "Validate assumption: Generic Title against general knowledge"
        )


def test_cpo_agent_run_with_nemawashi_and_canvas_models() -> None:
    """Test CPO agent run with influence network, VPC, and alternative analysis."""
    get_settings.cache_clear()

    mock_llm = MagicMock()
    mock_chain_result = MagicMock()
    mock_chain_result.content = "Detailed advice."
    mock_llm.invoke.return_value = mock_chain_result
    mock_llm.return_value = mock_chain_result

    with patch("src.agents.cpo.RAG") as MockRAG:
        mock_rag_instance = MockRAG.return_value
        # Return a deterministic string for RAG results
        mock_rag_instance.query.return_value = "Verified."

        agent = CPOAgent(
            llm=mock_llm,
            search_tool=MagicMock(),
            app_settings=get_settings(),
            rag_path="tests/temp_rag",
        )

        state = GlobalState(
            topic="Idea",
            selected_idea=LeanCanvas(
                id=1,
                title="Title",
                problem="Problem that has three words",
                solution="Solution that has three words",
                customer_segments="C",
                unique_value_prop="Unique value that has three words",
            ),
            influence_network=DenseInfluenceNetwork(
                matrix=[[1.0, 0.0], [0.0, 1.0]],
                stakeholders=[
                    Stakeholder(name="Sales", initial_support=0.2, stubbornness=0.8),
                    Stakeholder(name="Finance", initial_support=0.9, stubbornness=0.1),
                ],
            ),
            vpc=ValuePropositionCanvas(
                customer_profile=CustomerProfile(customer_jobs=["A"], pains=["B"], gains=["C"]),
                value_map=ValueMap(
                    products_and_services=["D"], pain_relievers=["E"], gain_creators=["F"]
                ),
                fit_evaluation="Good fit",
            ),
            alternative_analysis=AlternativeAnalysis(
                current_alternatives=[
                    AlternativeTool(
                        name="Tool", financial_cost="0", time_cost="10", ux_friction="high"
                    )
                ],
                switching_cost="High",
                ten_x_value="Fast",
            ),
        )

        res = agent.run(state)

        # Verify RAG query calls
        assert mock_rag_instance.query.call_count == 3

        # Call 1: Basic validation
        assert "Validate assumption" in mock_rag_instance.query.call_args_list[0][0][0]
        # Call 2: VPC validation
        assert "Validate VPC:" in mock_rag_instance.query.call_args_list[1][0][0]
        # Call 3: Alternative validation
        assert "Validate alternative analysis:" in mock_rag_instance.query.call_args_list[2][0][0]

        last_msg = res["debate_history"][-1]
        assert isinstance(last_msg, DialogueMessage)
        assert last_msg.role == Role.CPO


def test_cpo_agent_run_rag_error() -> None:
    """Test CPO agent run handles RAG error gracefully."""
    get_settings.cache_clear()

    mock_llm = MagicMock()
    mock_chain_result = MagicMock()
    mock_chain_result.content = "Fallback advice."
    mock_llm.invoke.return_value = mock_chain_result
    mock_llm.return_value = mock_chain_result

    with patch("src.agents.cpo.RAG") as MockRAG:
        mock_rag_instance = MockRAG.return_value
        # Force an error
        mock_rag_instance.query.side_effect = Exception("RAG Engine failure")

        agent = CPOAgent(
            llm=mock_llm,
            search_tool=MagicMock(),
            app_settings=get_settings(),
            rag_path="tests/temp_rag",
        )

        state = GlobalState(
            topic="Idea",
            selected_idea=LeanCanvas(
                id=1,
                title="Title",
                problem="Problem that has three words",
                solution="Solution that has three words",
                customer_segments="C",
                unique_value_prop="Unique value that has three words",
            ),
        )

        res = agent.run(state)

        # Should gracefully return the fallback error string without crashing the node
        last_msg = res["debate_history"][-1]
        assert isinstance(last_msg, DialogueMessage)
        assert last_msg.role == Role.CPO


def test_cpo_agent_run_generation_error() -> None:
    """Test CPO agent handles generation/prompt formatting errors gracefully."""
    get_settings.cache_clear()

    # Let LLM raise an exception
    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = Exception("LLM connection failed")

    with patch("src.agents.cpo.RAG") as MockRAG:
        mock_rag_instance = MockRAG.return_value
        mock_rag_instance.query.return_value = "Context"

        agent = CPOAgent(
            llm=mock_llm,
            search_tool=MagicMock(),
            app_settings=get_settings(),
            rag_path="tests/temp_rag",
        )

        state = GlobalState(
            topic="Idea",
            selected_idea=LeanCanvas(
                id=1,
                title="Title",
                problem="Problem that has three words",
                solution="Solution that has three words",
                customer_segments="C",
                unique_value_prop="Unique value that has three words",
            ),
        )

        # The base PersonaAgent handles exceptions, but run() has a broad except block
        res = agent.run(state)
        # if run broad catches error it returns dict with "error" key
        # let's assert either "error" is returned or the fallback works
        assert "error" in res or len(res.get("debate_history", [])) > 0
        if "error" in res:
            assert "LLM connection failed" in res["error"]
        assert "debate_history" in res


@patch("src.agents.cpo.RAG")
@patch("src.agents.cpo.BaseChatModel")
def test_cpo_agent_init(mock_llm: MagicMock, mock_rag: MagicMock) -> None:
    agent = CPOAgent(llm=mock_llm, search_tool=MagicMock(), app_settings=get_settings())
    assert agent.role == Role.CPO
    assert "Chief Product Officer" in agent.system_prompt
    assert "do not speak in the main meeting" in agent.system_prompt


@patch("src.agents.cpo.RAG")
@patch("src.agents.cpo.BaseChatModel")
def test_cpo_research(mock_llm: MagicMock, mock_rag: MagicMock) -> None:
    agent = CPOAgent(llm=mock_llm, search_tool=MagicMock(), app_settings=get_settings())
    # Mock RAG inside agent
    agent.rag = MagicMock()
    agent.rag.query.return_value = "Found customer data"

    result = agent._cached_research("SaaS Platform")
    assert result == "Found customer data"
    agent.rag.query.assert_called()
