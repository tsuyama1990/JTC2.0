from typing import Any
from unittest.mock import MagicMock

from src.agents.cpo import CPOAgent
from src.domain_models.simulation import Role


def test_cpo_agent_init() -> None:
    mock_llm = MagicMock()
    mock_rag = MagicMock()
    agent = CPOAgent(llm=mock_llm, rag=mock_rag)
    assert agent.role == Role.CPO
    assert "CPO" in agent.system_prompt


def test_cpo_research() -> None:
    mock_llm = MagicMock()
    mock_rag = MagicMock()
    agent = CPOAgent(llm=mock_llm, rag=mock_rag)

    # Mock RAG inside agent
    agent.rag.query.return_value = "Found customer data"  # type: ignore[attr-defined]

    class MockSimulationData:
        stakeholders: list[Any] = []  # noqa: RUF012

    # For now, to bypass the error regarding simulation_data
    # Pydantic may prevent setting unknown attributes, but we can set simulation_active=True
    # and we can patch the behavior or provide a simulation_data field if it exists.
    # Looking at the trace: AttributeError: 'GlobalState' object has no attribute 'simulation_data'. Did you mean: 'simulation_active'?
    # So we need to ensure our test does not crash on `state.simulation_data`.
    # Let's fix src/agents/cpo.py since it calls a non-existent attribute!
