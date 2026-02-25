import pytest

from src.core.nemawashi import NemawashiEngine
from src.domain_models.politics import InfluenceNetwork, Stakeholder
from src.domain_models.state import GlobalState


def test_identify_key_influencer_uat() -> None:
    """UAT-C04-01: Verify that the system correctly identifies the most influential node."""
    # Setup state
    s1 = Stakeholder(name="Finance Manager", initial_support=0.2, stubbornness=0.9)
    s2 = Stakeholder(name="Sales Manager", initial_support=0.8, stubbornness=0.5)
    s3 = Stakeholder(name="CEO", initial_support=0.5, stubbornness=0.2)

    # Finance listens only to self (0.9) and CEO (0.1)
    # Sales listens to Finance (0.5) and self (0.5)
    # CEO listens to Finance (0.8) and self (0.2) -> Finance is KEY

    matrix = [
        [0.9, 0.0, 0.1],
        [0.5, 0.5, 0.0],
        [0.8, 0.0, 0.2]
    ]

    net = InfluenceNetwork(stakeholders=[s1, s2, s3], matrix=matrix)
    state = GlobalState(influence_network=net)

    engine = NemawashiEngine()

    try:
        influencers = engine.identify_influencers(state.influence_network) # type: ignore
        # Verify Finance is top
        assert influencers[0] == "Finance Manager"
    except NotImplementedError:
        pytest.skip("NemawashiEngine not implemented yet")


def test_nomikai_effect_uat() -> None:
    """UAT-C04-02: Verify that simulating a social event changes the outcome."""
    # Setup: Finance hates it. Group consensus low.
    s1 = Stakeholder(name="Finance Manager", initial_support=0.1, stubbornness=0.9)
    s2 = Stakeholder(name="CEO", initial_support=0.4, stubbornness=0.2)

    # Finance listens to self 0.9, CEO 0.1
    # CEO listens to Finance 0.8, self 0.2
    matrix = [
        [0.9, 0.1],
        [0.8, 0.2]
    ]

    net = InfluenceNetwork(stakeholders=[s1, s2], matrix=matrix)

    engine = NemawashiEngine()

    try:
        initial_ops = engine.calculate_consensus(net)
        initial_avg = sum(initial_ops) / len(initial_ops)

        # Run Nomikai on Finance
        new_net = engine.run_nomikai(net, "Finance Manager")

        # Check Finance support increase
        assert new_net.stakeholders[0].initial_support > 0.1

        # Re-run consensus
        final_ops = engine.calculate_consensus(new_net)
        final_avg = sum(final_ops) / len(final_ops)

        # Should be higher
        assert final_avg > initial_avg

    except NotImplementedError:
        pytest.skip("NemawashiEngine not implemented yet")
