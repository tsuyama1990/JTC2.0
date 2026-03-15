import pytest
from pydantic import ValidationError

from src.domain_models.politics import DenseInfluenceNetwork, Stakeholder


def test_valid_network() -> None:
    """Test creating a valid influence network."""
    s1 = Stakeholder(name="Alice", initial_support=0.5, stubbornness=0.2)
    s2 = Stakeholder(name="Bob", initial_support=0.8, stubbornness=0.1)

    matrix = [[1.0, 0.0], [0.5, 0.5]]

    net = DenseInfluenceNetwork(stakeholders=[s1, s2], matrix=matrix)
    assert len(net.stakeholders) == 2
    assert net.matrix == matrix


def test_invalid_matrix_values() -> None:
    """Test that matrix values must be [0, 1]."""
    s1 = Stakeholder(name="Alice", initial_support=0.5, stubbornness=0.2)
    matrix = [[1.5]]  # Invalid value

    with pytest.raises(ValidationError) as exc:
        DenseInfluenceNetwork(stakeholders=[s1], matrix=matrix)
    assert "Matrix values must be between 0.0 and 1.0" in str(exc.value)


def test_matrix_dimension_mismatch() -> None:
    """Test that matrix dimensions match stakeholder count."""
    s1 = Stakeholder(name="Alice", initial_support=0.5, stubbornness=0.2)
    s2 = Stakeholder(name="Bob", initial_support=0.8, stubbornness=0.1)

    # 1x1 matrix for 2 stakeholders
    matrix = [[1.0]]

    with pytest.raises(ValidationError) as exc:
        DenseInfluenceNetwork(stakeholders=[s1, s2], matrix=matrix)
    assert "Matrix row count must match stakeholder count" in str(exc.value)


def test_matrix_shape_mismatch() -> None:
    """Test that matrix must be square."""
    s1 = Stakeholder(name="Alice", initial_support=0.5, stubbornness=0.2)
    s2 = Stakeholder(name="Bob", initial_support=0.8, stubbornness=0.1)

    # 2x1 matrix
    matrix = [[1.0], [0.5]]

    with pytest.raises(ValidationError) as exc:
        DenseInfluenceNetwork(stakeholders=[s1, s2], matrix=matrix)
    assert "Matrix must be square" in str(exc.value)


def test_stakeholder_validation() -> None:
    """Test stakeholder field validation."""
    with pytest.raises(ValidationError):
        Stakeholder(name="", initial_support=0.5, stubbornness=0.1)

    with pytest.raises(ValidationError):
        Stakeholder(name="Alice", initial_support=1.5, stubbornness=0.1)

    with pytest.raises(ValidationError):
        Stakeholder(name="Alice", initial_support=0.5, stubbornness=-0.1)
