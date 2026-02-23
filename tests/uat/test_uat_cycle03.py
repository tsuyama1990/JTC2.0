import os
from unittest.mock import MagicMock, patch

import pytest

from src.core.config import get_settings
from src.domain_models.lean_canvas import LeanCanvas
from src.domain_models.state import GlobalState
from src.domain_models.transcript import Transcript
from tests.conftest import DUMMY_ENV_VARS


@patch.dict(os.environ, DUMMY_ENV_VARS)
@patch("src.agents.cpo.RAG")
@patch("src.agents.cpo.ChatOpenAI")
def test_uat_c03_01_mom_test_failure(mock_llm: MagicMock, mock_rag_cls: MagicMock) -> None:
    """
    Scenario 1: Transcript Injection and 'Mom Test' Failure.
    Verify that injecting negative customer feedback causes the CPO to suggest a pivot.
    """
    get_settings.cache_clear()
    try:
        from src.agents.cpo import CPOAgent
    except ImportError:
        pytest.skip("CPOAgent not implemented yet")

    # Setup
    state = GlobalState(
        topic="Subscription Service",
        transcripts=[
            Transcript(source="interview.txt", content="I would never pay for this.", date="2023-10-27")
        ],
        selected_idea=LeanCanvas(
            id=1,
            title="Subscription Service Idea",
            problem="Users hate current subscriptions.",
            solution="A pay-as-you-go model.",
            customer_segments="Freelancers and SMBs.",
            unique_value_prop="No commitment required."
        )
    )

    # Mock RAG query response
    mock_rag_instance = mock_rag_cls.return_value
    mock_rag_instance.query.return_value = "Customer says: I would never pay for this."

    # Mock LLM response to simulate CPO advice based on RAG
    mock_llm_instance = mock_llm.return_value

    # We patch _generate_response to avoid dealing with LangChain piping mocks
    with patch.object(CPOAgent, "_generate_response", return_value="Based on the transcript... You should pivot.") as mock_gen:
        # Run CPO Agent
        cpo = CPOAgent(mock_llm_instance)
        result = cpo.run(state)

        # Verify RAG was consulted
        mock_rag_instance.query.assert_called()

        # Verify RAG output was passed to _generate_response
        args, _ = mock_gen.call_args
        assert args[1] == "Customer says: I would never pay for this."

        # Verify output
        assert "debate_history" in result
        last_msg = result["debate_history"][-1]
        assert "pivot" in last_msg.content.lower()


@patch.dict(os.environ, DUMMY_ENV_VARS)
@patch("src.agents.cpo.RAG")
@patch("src.agents.cpo.ChatOpenAI")
def test_uat_c03_02_validation_success(mock_llm: MagicMock, mock_rag_cls: MagicMock) -> None:
    """
    Scenario 2: Validation Success.
    Verify that positive feedback reinforces the plan.
    """
    get_settings.cache_clear()
    try:
        from src.agents.cpo import CPOAgent
    except ImportError:
        pytest.skip("CPOAgent not implemented yet")

    # Setup
    state = GlobalState(
        topic="Great Idea",
        transcripts=[
            Transcript(source="interview_positive.txt", content="I love this!", date="2023-10-27")
        ],
        selected_idea=LeanCanvas(
            id=1,
            title="Great Idea Title",
            problem="Big headache for users.",
            solution="Simple and effective fix.",
            customer_segments="Everyone needs this.",
            unique_value_prop="Best in class solution."
        )
    )

    # Mock RAG query response
    mock_rag_instance = mock_rag_cls.return_value
    mock_rag_instance.query.return_value = "Customer says: I love this!"

    # Mock LLM response
    mock_llm_instance = mock_llm.return_value

    with patch.object(CPOAgent, "_generate_response", return_value="Customer validation is strong. Proceed.") as mock_gen:
        # Run CPO Agent
        cpo = CPOAgent(mock_llm_instance)
        result = cpo.run(state)

        # Verify
        mock_rag_instance.query.assert_called()

        # Verify RAG output passed
        args, _ = mock_gen.call_args
        assert args[1] == "Customer says: I love this!"

        last_msg = result["debate_history"][-1]
        assert "strong" in last_msg.content.lower()
