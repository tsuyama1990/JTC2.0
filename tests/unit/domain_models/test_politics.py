import pytest
from pydantic import ValidationError

from src.domain_models.politics import InfluenceNetwork, Stakeholder


def test_stakeholder_validation() -> None:
    # Valid
    s = Stakeholder(name="Test", initial_support=0.5, stubbornness=0.1)
    assert s.name == "Test"
    assert s.initial_support == 0.5
    assert s.stubbornness == 0.1

    # Invalid support
    with pytest.raises(ValidationError):
        Stakeholder(name="Test", initial_support=1.5, stubbornness=0.1)

    with pytest.raises(ValidationError):
        Stakeholder(name="Test", initial_support=-0.1, stubbornness=0.1)

    # Invalid stubbornness
    with pytest.raises(ValidationError):
        Stakeholder(name="Test", initial_support=0.5, stubbornness=1.1)


def test_influence_network_validation() -> None:
    s1 = Stakeholder(name="A", initial_support=0.5, stubbornness=0.5)
    s2 = Stakeholder(name="B", initial_support=0.5, stubbornness=0.5)

    # Valid matrix
    matrix = [[0.5, 0.5], [0.5, 0.5]]
    net = InfluenceNetwork(stakeholders=[s1, s2], matrix=matrix)
    assert len(net.stakeholders) == 2
    assert net.matrix == matrix

    # Invalid matrix type (pydantic checks types, not logic like row stochasticity yet)
    with pytest.raises(ValidationError):
        InfluenceNetwork(stakeholders=[s1], matrix="invalid")  # type: ignore[arg-type]

    # Extra fields forbidden
    with pytest.raises(ValidationError):
        InfluenceNetwork(stakeholders=[], matrix=[], extra_field="bad")  # type: ignore[call-arg]
