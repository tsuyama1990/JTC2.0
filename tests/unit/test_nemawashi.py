import numpy as np
import pytest

from src.core.nemawashi import NemawashiEngine
from src.domain_models.politics import InfluenceNetwork, Stakeholder


@pytest.fixture
def sample_network() -> InfluenceNetwork:
    """A small test network."""
    # S1 (Finance): Stubborn, initial low support (0.2)
    s1 = Stakeholder(name="Finance", initial_support=0.2, stubbornness=0.9)
    # S2 (Sales): Loves it (0.8), less stubborn (0.5), listens to Finance (0.5)
    s2 = Stakeholder(name="Sales", initial_support=0.8, stubbornness=0.5)

    # Adjacency Matrix (Row-stochastic)
    # Row 0 (Finance): [0.9 (Self), 0.1 (Sales)]
    # Row 1 (Sales): [0.5 (Finance), 0.5 (Self)]
    matrix = [
        [0.9, 0.1],
        [0.5, 0.5]
    ]
    return InfluenceNetwork(stakeholders=[s1, s2], matrix=matrix)


def test_calculate_consensus_convergence(sample_network: InfluenceNetwork) -> None:
    """Ensure opinions converge over time."""
    engine = NemawashiEngine()

    final_opinions = engine.calculate_consensus(sample_network)

    assert len(final_opinions) == 2
    # Finance started 0.2, Sales 0.8
    # Finance moves slowly up, Sales moves fast down
    assert final_opinions[0] > 0.2
    assert final_opinions[1] < 0.8
    # Finance dominates
    assert final_opinions[1] < 0.6


def test_identify_influencers(sample_network: InfluenceNetwork) -> None:
    """Ensure key influencers are identified."""
    engine = NemawashiEngine()

    influencers = engine.identify_influencers(sample_network)
    assert influencers[0] == "Finance"


def test_run_nomikai_immutability(sample_network: InfluenceNetwork) -> None:
    """Ensure run_nomikai returns a new object and modifies state."""
    engine = NemawashiEngine()

    new_net = engine.run_nomikai(sample_network, "Finance")

    assert new_net is not sample_network
    # Verify immutability
    assert sample_network.stakeholders[0].initial_support == 0.2

    # Verify changes in new network
    assert new_net.stakeholders[0].initial_support > 0.2
    assert new_net.stakeholders[0].stubbornness < 0.9


def test_large_network_safety() -> None:
    """Ensure engine handles larger networks without crashing."""
    n = 50
    # Use a connected graph (cycle) to avoid NetworkError
    stakeholders = [Stakeholder(name=f"S{i}", initial_support=0.5, stubbornness=0.1) for i in range(n)]

    # Construct cycle matrix
    matrix = np.zeros((n, n))
    for i in range(n):
        matrix[i][i] = 0.5 # Self
        matrix[i][(i+1)%n] = 0.5 # Next neighbor

    net = InfluenceNetwork(stakeholders=stakeholders, matrix=matrix.tolist())

    engine = NemawashiEngine()
    engine.calculate_consensus(net)
