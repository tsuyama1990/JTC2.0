import pytest
from pydantic import ValidationError

from src.core.constants import (
    ERR_MATRIX_SHAPE,
    ERR_MATRIX_VALUES,
    ERR_STAKEHOLDER_MISMATCH,
)
from src.domain_models.politics import InfluenceNetwork, SparseMatrixEntry, Stakeholder


def test_valid_network() -> None:
    """Test creating a valid influence network."""
    s1 = Stakeholder(name="Alice", initial_support=0.5, stubbornness=0.2)
    s2 = Stakeholder(name="Bob", initial_support=0.8, stubbornness=0.1)

    matrix = [[1.0, 0.0], [0.5, 0.5]]

    net = InfluenceNetwork(stakeholders=[s1, s2], matrix=matrix)
    assert len(net.stakeholders) == 2
    assert net.matrix == matrix


def test_invalid_matrix_values() -> None:
    """Test that matrix values must be [0, 1]."""
    s1 = Stakeholder(name="Alice", initial_support=0.5, stubbornness=0.2)
    matrix = [[1.5]]  # Invalid value

    with pytest.raises(ValidationError) as exc:
        InfluenceNetwork(stakeholders=[s1], matrix=matrix)
    assert ERR_MATRIX_VALUES in str(exc.value)


def test_matrix_dimension_mismatch() -> None:
    """Test that matrix dimensions match stakeholder count."""
    s1 = Stakeholder(name="Alice", initial_support=0.5, stubbornness=0.2)
    s2 = Stakeholder(name="Bob", initial_support=0.8, stubbornness=0.1)

    # 1x1 matrix for 2 stakeholders
    matrix = [[1.0]]

    with pytest.raises(ValidationError) as exc:
        InfluenceNetwork(stakeholders=[s1, s2], matrix=matrix)
    assert ERR_STAKEHOLDER_MISMATCH in str(exc.value)


def test_matrix_shape_mismatch() -> None:
    """Test that matrix must be square."""
    s1 = Stakeholder(name="Alice", initial_support=0.5, stubbornness=0.2)
    s2 = Stakeholder(name="Bob", initial_support=0.8, stubbornness=0.1)

    # 2x1 matrix
    matrix = [[1.0], [0.5]]

    with pytest.raises(ValidationError) as exc:
        InfluenceNetwork(stakeholders=[s1, s2], matrix=matrix)
    assert ERR_MATRIX_SHAPE in str(exc.value)


def test_stakeholder_validation() -> None:
    """Test stakeholder field validation."""
    with pytest.raises(ValidationError):
        Stakeholder(name="", initial_support=0.5, stubbornness=0.1)

    with pytest.raises(ValidationError):
        Stakeholder(name="Alice", initial_support=1.5, stubbornness=0.1)

    with pytest.raises(ValidationError):
        Stakeholder(name="Alice", initial_support=0.5, stubbornness=-0.1)


def test_sparse_matrix() -> None:
    s1 = Stakeholder(name="Alice", initial_support=0.5, stubbornness=0.2)
    s2 = Stakeholder(name="Bob", initial_support=0.8, stubbornness=0.1)

    # Valid sparse matrix
    matrix = [
        SparseMatrixEntry(row=0, col=0, val=0.5),
        SparseMatrixEntry(row=0, col=1, val=0.5),
        SparseMatrixEntry(row=1, col=0, val=0.2),
        SparseMatrixEntry(row=1, col=1, val=0.8),
    ]

    net = InfluenceNetwork(stakeholders=[s1, s2], matrix=matrix)
    assert len(net.matrix) == 4


def test_invalid_sparse_matrix_shape() -> None:
    s1 = Stakeholder(name="Alice", initial_support=0.5, stubbornness=0.2)
    s2 = Stakeholder(name="Bob", initial_support=0.8, stubbornness=0.1)

    # Invalid sparse matrix (col index out of bounds)
    matrix = [
        SparseMatrixEntry(row=0, col=0, val=0.5),
        SparseMatrixEntry(row=0, col=2, val=0.5),  # Out of bounds
        SparseMatrixEntry(row=1, col=0, val=0.2),
        SparseMatrixEntry(row=1, col=1, val=0.8),
    ]

    with pytest.raises(ValidationError) as exc:
        InfluenceNetwork(stakeholders=[s1, s2], matrix=matrix)
    assert ERR_MATRIX_SHAPE in str(exc.value)


def test_invalid_sparse_matrix_stochasticity() -> None:
    s1 = Stakeholder(name="Alice", initial_support=0.5, stubbornness=0.2)
    s2 = Stakeholder(name="Bob", initial_support=0.8, stubbornness=0.1)

    # Invalid sparse matrix (row 0 sums to 0.8)
    matrix = [
        SparseMatrixEntry(row=0, col=0, val=0.5),
        SparseMatrixEntry(row=0, col=1, val=0.3),
        SparseMatrixEntry(row=1, col=0, val=0.2),
        SparseMatrixEntry(row=1, col=1, val=0.8),
    ]

    with pytest.raises(ValidationError):
        InfluenceNetwork(stakeholders=[s1, s2], matrix=matrix)
