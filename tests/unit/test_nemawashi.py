from unittest.mock import patch

import pytest
from scipy.sparse import csr_matrix

from src.core.exceptions import ValidationError
from src.core.nemawashi.consensus import ConsensusEngine
from src.domain_models.politics import InfluenceNetwork, SparseMatrixEntry, Stakeholder


def test_consensus_conversion_failure() -> None:
    """Test that matrix conversion failures are handled gracefully."""
    # Create invalid sparse entries (out of bounds)
    # This should be caught by domain model, but if we force it or mock it
    # Ideally domain model catches it.
    # Let's mock coo_matrix to raise an error

    s1 = Stakeholder(name="A", initial_support=0.5, stubbornness=0.5)
    network = InfluenceNetwork(
        stakeholders=[s1],
        matrix=[SparseMatrixEntry(row=0, col=0, val=1.0)]
    )

    engine = ConsensusEngine()

    with patch("src.core.nemawashi.consensus.coo_matrix", side_effect=Exception("Conversion Boom")):
        with pytest.raises(ValidationError, match="Failed to build sparse matrix"):
            engine.calculate_consensus(network)

def test_consensus_dense_conversion_failure() -> None:
    """Test dense matrix conversion failure."""
    s1 = Stakeholder(name="A", initial_support=0.5, stubbornness=0.5)
    # Dense matrix
    network = InfluenceNetwork(
        stakeholders=[s1],
        matrix=[[1.0]]
    )

    engine = ConsensusEngine()

    with patch("src.core.nemawashi.consensus.csr_matrix", side_effect=Exception("Dense Boom")):
        with pytest.raises(ValidationError, match="Failed to convert dense matrix"):
            engine.calculate_consensus(network)

def test_consensus_stochasticity_check_failure() -> None:
    """Test that runtime stochasticity check catches invalid matrices."""
    s1 = Stakeholder(name="A", initial_support=0.5, stubbornness=0.5)
    network = InfluenceNetwork(
        stakeholders=[s1],
        matrix=[[1.0]]
    )

    engine = ConsensusEngine()

    # Mock the built matrix to be invalid (row sum != 1.0)
    # We can patch _build_sparse_matrix to return a bad matrix
    bad_matrix = csr_matrix([[0.9]]) # Sum is 0.9

    with patch.object(engine, "_build_sparse_matrix", return_value=bad_matrix):
        with pytest.raises(ValidationError, match="Influence matrix rows must sum to 1.0"):
            engine.calculate_consensus(network)

def test_consensus_calculation() -> None:
    """Test standard calculation flow."""
    s1 = Stakeholder(name="A", initial_support=0.0, stubbornness=0.0)
    s2 = Stakeholder(name="B", initial_support=1.0, stubbornness=1.0)
    # A follows B (100%), B follows self (100%)
    entries = [
        SparseMatrixEntry(row=0, col=1, val=1.0),
        SparseMatrixEntry(row=1, col=1, val=1.0)
    ]
    network = InfluenceNetwork(stakeholders=[s1, s2], matrix=entries)

    engine = ConsensusEngine()
    result = engine.calculate_consensus(network)

    assert result[0] > 0.9 # A should converge to B
    assert result[1] == 1.0
