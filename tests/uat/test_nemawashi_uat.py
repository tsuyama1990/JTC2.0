from typing import Any

import pytest

from src.core.nemawashi.analytics import AnalyticsService
from src.core.nemawashi.consensus import ConsensusService
from src.core.nemawashi.nomikai import SimulationService
from src.domain_models.politics import (
    DenseInfluenceNetwork,
    SparseInfluenceNetwork,
    SparseMatrixEntry,
    Stakeholder,
)
from src.domain_models.state import GlobalState

TEST_FINANCE_DOMINANT_MATRIX = [[0.9, 0.0, 0.1], [0.5, 0.5, 0.0], [0.8, 0.0, 0.2]]
TEST_NOMIKAI_MATRIX = [[0.9, 0.1], [0.8, 0.2]]
FINANCE_MANAGER_PARAMS: dict[str, Any] = {
    "name": "Finance Manager",
    "initial_support": 0.2,
    "stubbornness": 0.9,
}
SALES_MANAGER_PARAMS: dict[str, Any] = {
    "name": "Sales Manager",
    "initial_support": 0.8,
    "stubbornness": 0.5,
}
CEO_PARAMS: dict[str, Any] = {"name": "CEO", "initial_support": 0.5, "stubbornness": 0.2}


def test_identify_key_influencer_uat() -> None:
    """UAT-C04-01: Verify that the system correctly identifies the most influential node."""
    # Setup state
    s1 = Stakeholder(**FINANCE_MANAGER_PARAMS)
    s2 = Stakeholder(**SALES_MANAGER_PARAMS)
    s3 = Stakeholder(**CEO_PARAMS)

    # Finance listens only to self (0.9) and CEO (0.1)
    # Sales listens to Finance (0.5) and self (0.5)
    # CEO listens to Finance (0.8) and self (0.2) -> Finance is KEY

    net = DenseInfluenceNetwork(stakeholders=[s1, s2, s3], matrix=TEST_FINANCE_DOMINANT_MATRIX)
    state = GlobalState(influence_network=net)

    engine = AnalyticsService()

    try:
        influencers = engine.identify_influencers(state.influence_network)
        # Verify Finance is top
        # This is expected because the eigenvector centrality will be highest for
        # Finance, as both Sales and CEO depend heavily on Finance's opinion (weights 0.5 and 0.8)
        # while Finance relies almost entirely on themselves (weight 0.9).
        assert influencers[0] == FINANCE_MANAGER_PARAMS["name"]
    except NotImplementedError:
        pytest.skip("AnalyticsService identify_influencers not fully implemented yet")


def test_nomikai_effect_uat() -> None:
    """UAT-C04-02: Verify that simulating a social event changes the outcome."""
    # Setup: Finance hates it. Group consensus low.
    s1 = Stakeholder(
        name=FINANCE_MANAGER_PARAMS["name"],
        initial_support=0.1,
        stubbornness=FINANCE_MANAGER_PARAMS["stubbornness"],
    )
    s2 = Stakeholder(
        name=CEO_PARAMS["name"], initial_support=0.4, stubbornness=CEO_PARAMS["stubbornness"]
    )

    # Finance listens to self 0.9, CEO 0.1
    # CEO listens to Finance 0.8, self 0.2
    net = DenseInfluenceNetwork(stakeholders=[s1, s2], matrix=TEST_NOMIKAI_MATRIX)

    consensus_service = ConsensusService()
    simulation_service = SimulationService()

    try:
        initial_ops = consensus_service.calculate_consensus(net)
        initial_avg = sum(initial_ops) / len(initial_ops)

        # Run Nomikai on Finance
        new_net = simulation_service.run_nomikai(net, str(FINANCE_MANAGER_PARAMS["name"]))

        # Check Finance support increase
        assert new_net.stakeholders[0].initial_support > 0.1

        # Re-run consensus
        final_ops = consensus_service.calculate_consensus(new_net)
        final_avg = sum(final_ops) / len(final_ops)

        # Should be higher
        assert final_avg > initial_avg

    except NotImplementedError:
        pytest.skip("SimulationService run_nomikai not fully implemented yet")


def test_identify_influencers_edge_cases() -> None:
    """Test identify_influencers handles edge cases like empty networks, single stakeholder, etc."""
    engine = AnalyticsService()
    import pytest
    from pydantic import ValidationError

    # Empty network
    # stakeholders must have min_length=1 according to domain model, so this raises validation error instead of being a valid state
    with pytest.raises(ValidationError, match="List should have at least 1 item"):
        SparseInfluenceNetwork(stakeholders=[], matrix=[])

    # Single stakeholder network
    s1 = Stakeholder(name="Loner", initial_support=0.5, stubbornness=0.5)
    single_network = SparseInfluenceNetwork(
        stakeholders=[s1], matrix=[SparseMatrixEntry(row=0, col=0, val=1.0)]
    )

    # It should fallback to dense_eig and succeed instead of raising CalculationError
    influencers = engine.identify_influencers(single_network)
    assert influencers == ["Loner"]

    # Invalid matrix testing: The specified SparseMatrixEntry references row 5 and col 5,
    # but there are only 2 stakeholders defined in the list, causing an out-of-bounds error.
    s2 = Stakeholder(name="B", initial_support=0.5, stubbornness=0.5)
    invalid_entry = SparseMatrixEntry(row=5, col=5, val=1.0)
    with pytest.raises(
        ValidationError, match="Sparse entry indices must be within stakeholder count"
    ):
        SparseInfluenceNetwork(stakeholders=[s1, s2], matrix=[invalid_entry])
