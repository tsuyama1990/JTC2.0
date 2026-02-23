import pytest

from src.core.nemawashi import NemawashiEngine
from src.domain_models.politics import InfluenceNetwork, Stakeholder


def test_degroot_consensus() -> None:
    # A listens to B (0.5) and self (0.5).
    # B listens to A (0.5) and self (0.5).
    # Initial: A=0, B=1.
    s1 = Stakeholder(name="A", initial_support=0.0, stubbornness=0.5)
    s2 = Stakeholder(name="B", initial_support=1.0, stubbornness=0.5)

    matrix = [[0.5, 0.5], [0.5, 0.5]]
    net = InfluenceNetwork(stakeholders=[s1, s2], matrix=matrix)

    engine = NemawashiEngine()
    result = engine.calculate_consensus(net, max_steps=10)

    # Floating point comparison
    assert abs(result["A"] - 0.5) < 1e-6
    assert abs(result["B"] - 0.5) < 1e-6


def test_nomikai_effect() -> None:
    s1 = Stakeholder(name="New Employee", initial_support=1.0, stubbornness=1.0)
    s2 = Stakeholder(name="Target", initial_support=0.0, stubbornness=1.0)

    # Target ignores New Employee initially
    matrix = [
        [1.0, 0.0],  # New Employee listens to self
        [0.0, 1.0],  # Target listens to self
    ]

    net = InfluenceNetwork(stakeholders=[s1, s2], matrix=matrix)
    engine = NemawashiEngine()

    # Before nomikai
    res_before = engine.calculate_consensus(net)
    assert res_before["Target"] == 0.0

    # Run Nomikai
    updated_net = engine.run_nomikai(net, target_name="Target", influencer_name="New Employee")

    # Check matrix update
    # Target is index 1, New Employee is index 0.
    target_row = updated_net.matrix[1]
    assert target_row[0] > 0.0  # Weight for New Employee increased
    assert target_row[1] < 1.0  # Stubbornness decreased

    # New consensus
    res_after = engine.calculate_consensus(updated_net)
    assert res_after["Target"] > 0.0


def test_zero_sum_rows() -> None:
    s1 = Stakeholder(name="A", initial_support=0.5, stubbornness=0.5)
    matrix = [[0.0]]  # Zero sum row
    net = InfluenceNetwork(stakeholders=[s1], matrix=matrix)
    engine = NemawashiEngine()
    result = engine.calculate_consensus(net)
    # The engine should normalize the row to [1.0] (self loop)
    assert result["A"] == 0.5


def test_nomikai_invalid_stakeholder(caplog: pytest.LogCaptureFixture) -> None:
    s1 = Stakeholder(name="A", initial_support=0.5, stubbornness=0.5)
    matrix = [[1.0]]
    net = InfluenceNetwork(stakeholders=[s1], matrix=matrix)
    engine = NemawashiEngine()

    # We expect an exception log when stakeholder is not found
    updated_net = engine.run_nomikai(net, "NonExistent", "A")
    assert updated_net is net  # Should return original
    assert "Stakeholder not found" in caplog.text


def test_nomikai_clamping() -> None:
    # Force stubbornness to go below 0
    s1 = Stakeholder(name="A", initial_support=0.5, stubbornness=0.1)  # Low stubbornness
    s2 = Stakeholder(name="B", initial_support=0.5, stubbornness=0.9)

    # A listens to A (0.1) and B (0.9)
    # B listens to B (1.0)
    matrix = [
        [0.1, 0.9],
        [0.0, 1.0],
    ]
    net = InfluenceNetwork(stakeholders=[s1, s2], matrix=matrix)
    engine = NemawashiEngine()

    # Nomikai on A from B. Boost is 0.3.
    # New self weight = 0.1 - 0.3 = -0.2 -> Clamped to 0.
    res = engine.run_nomikai(net, "A", "B")

    # A is index 0
    assert res.matrix[0][0] == 0.0
    assert res.stakeholders[0].stubbornness == 0.0


def test_empty_network() -> None:
    net = InfluenceNetwork(stakeholders=[], matrix=[])
    engine = NemawashiEngine()
    assert engine.calculate_consensus(net) == {}
    assert engine.identify_influencers(net) == []
