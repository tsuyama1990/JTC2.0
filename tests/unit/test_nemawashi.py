import math
from unittest.mock import patch

import numpy as np
import pytest
from scipy.sparse import csr_matrix

from src.core.config import NemawashiConfig
from src.core.exceptions import CalculationError, ValidationError
from src.core.nemawashi.analytics import InfluenceAnalyzer
from src.core.nemawashi.consensus import ConsensusEngine
from src.core.nemawashi.engine import NemawashiEngine
from src.core.nemawashi.nomikai import NomikaiSimulator
from src.core.nemawashi.utils import NemawashiUtils
from src.domain_models.politics import InfluenceNetwork, SparseMatrixEntry, Stakeholder


def test_consensus_conversion_failure() -> None:
    """Test that matrix conversion failures are handled gracefully."""
    # Create invalid sparse entries (out of bounds)
    # This should be caught by domain model, but if we force it or mock it
    # Ideally domain model catches it.
    # Let's mock coo_matrix to raise an error

    s1 = Stakeholder(name="A", initial_support=0.5, stubbornness=0.5)
    network = InfluenceNetwork(stakeholders=[s1], matrix=[SparseMatrixEntry(row=0, col=0, val=1.0)])

    engine = ConsensusEngine()

    with (
        patch("src.core.nemawashi.utils.coo_matrix", side_effect=Exception("Conversion Boom")),
        pytest.raises(ValidationError, match="Failed to build sparse matrix"),
    ):
        engine.calculate_consensus(network)


def test_consensus_dense_conversion_failure() -> None:
    """Test dense matrix conversion failure."""
    s1 = Stakeholder(name="A", initial_support=0.5, stubbornness=0.5)
    # Dense matrix
    network = InfluenceNetwork(stakeholders=[s1], matrix=[[1.0]])

    engine = ConsensusEngine()

    with (
        patch("src.core.nemawashi.utils.csr_matrix", side_effect=Exception("Dense Boom")),
        pytest.raises(ValidationError, match="Failed to convert dense matrix"),
    ):
        engine.calculate_consensus(network)


def test_consensus_stochasticity_check_failure() -> None:
    """Test that runtime stochasticity check catches invalid matrices."""
    s1 = Stakeholder(name="A", initial_support=0.5, stubbornness=0.5)
    network = InfluenceNetwork(stakeholders=[s1], matrix=[[1.0]])

    engine = ConsensusEngine()

    # Mock the built matrix to be invalid (row sum != 1.0)
    # We can patch _build_sparse_matrix to return a bad matrix
    bad_matrix = csr_matrix([[0.9]])  # Sum is 0.9

    with (
        patch(
            "src.core.nemawashi.consensus.NemawashiUtils.build_sparse_matrix",
            return_value=bad_matrix,
        ),
        pytest.raises(ValidationError, match="Influence matrix rows must sum to 1.0"),
    ):
        engine.calculate_consensus(network)


def test_consensus_calculation() -> None:
    """Test standard calculation flow."""
    s1 = Stakeholder(name="A", initial_support=0.0, stubbornness=0.0)
    s2 = Stakeholder(name="B", initial_support=1.0, stubbornness=1.0)
    # A follows B (100%), B follows self (100%)
    entries = [SparseMatrixEntry(row=0, col=1, val=1.0), SparseMatrixEntry(row=1, col=1, val=1.0)]
    network = InfluenceNetwork(stakeholders=[s1, s2], matrix=entries)

    engine = ConsensusEngine()
    result = engine.calculate_consensus(network)

    assert result[0] > 0.9  # A should converge to B
    assert result[1] == 1.0


def test_identify_influencers_empty() -> None:
    """Test identify influencers on an empty network."""
    # Test skipped or altered: network requires at least 1 stakeholder.
    s1 = Stakeholder(name="A", initial_support=0.5, stubbornness=0.5)
    network = InfluenceNetwork(stakeholders=[s1], matrix=[[1.0]])
    analyzer = InfluenceAnalyzer()
    assert analyzer.identify_influencers(network) == ["A"]


def test_identify_influencers_dense() -> None:
    """Test identify influencers using a dense matrix."""
    s1 = Stakeholder(name="A", initial_support=0.5, stubbornness=0.5)
    s2 = Stakeholder(name="B", initial_support=0.5, stubbornness=0.5)
    network = InfluenceNetwork(stakeholders=[s1, s2], matrix=[[0.8, 0.2], [0.1, 0.9]])
    analyzer = InfluenceAnalyzer()

    influencers = analyzer.identify_influencers(network)
    assert influencers == ["B", "A"]  # B has 0.9 self and 0.2 from A, so B > A


def test_identify_influencers_sparse() -> None:
    """Test identify influencers using a sparse matrix."""
    s1 = Stakeholder(name="A", initial_support=0.5, stubbornness=0.5)
    s2 = Stakeholder(name="B", initial_support=0.5, stubbornness=0.5)
    s3 = Stakeholder(name="C", initial_support=0.5, stubbornness=0.5)
    entries = [
        SparseMatrixEntry(row=0, col=0, val=0.8),
        SparseMatrixEntry(row=0, col=1, val=0.1),
        SparseMatrixEntry(row=0, col=2, val=0.1),
        SparseMatrixEntry(row=1, col=0, val=0.0),
        SparseMatrixEntry(row=1, col=1, val=0.9),
        SparseMatrixEntry(row=1, col=2, val=0.1),
        SparseMatrixEntry(row=2, col=0, val=0.0),
        SparseMatrixEntry(row=2, col=1, val=0.1),
        SparseMatrixEntry(row=2, col=2, val=0.9),
    ]
    network = InfluenceNetwork(stakeholders=[s1, s2, s3], matrix=entries)
    analyzer = InfluenceAnalyzer()

    influencers = analyzer.identify_influencers(network)
    assert len(influencers) == 3


def test_is_connected_dense() -> None:
    """Test connectivity checker."""
    analyzer = InfluenceAnalyzer()
    assert analyzer.is_connected([]) is False
    assert analyzer.is_connected([[1.0]]) is True
    assert analyzer.is_connected([[1.0, 0.0], [0.0, 1.0]]) is False
    assert analyzer.is_connected([[0.5, 0.5], [0.5, 0.5]]) is True


def test_run_nomikai_not_found() -> None:
    """Test nomikai simulator raises ValidationError when target not found."""
    s1 = Stakeholder(name="A", initial_support=0.5, stubbornness=0.5)
    network = InfluenceNetwork(stakeholders=[s1], matrix=[[1.0]])
    simulator = NomikaiSimulator()
    with pytest.raises(ValidationError, match="Target B not found."):
        simulator.run_nomikai(network, "B")


def test_run_nomikai_dense() -> None:
    """Test nomikai simulator on dense matrix."""
    s1 = Stakeholder(name="A", initial_support=0.2, stubbornness=0.9)
    s2 = Stakeholder(name="B", initial_support=0.2, stubbornness=0.9)
    matrix = [[0.9, 0.1], [0.1, 0.9]]
    network = InfluenceNetwork(stakeholders=[s1, s2], matrix=matrix)

    settings = NemawashiConfig()
    settings.nomikai_boost = 0.5
    settings.nomikai_reduction = 0.2
    simulator = NomikaiSimulator(settings=settings)

    new_net = simulator.run_nomikai(network, "A")
    # A's initial support increases: 0.2 + (0.8 * 0.5) = 0.6
    assert math.isclose(new_net.stakeholders[0].initial_support, 0.6, rel_tol=1e-5)
    # A's self weight reduces: 0.9 - 0.2 = 0.7
    # 0.2 difference distributed to 1 other person (B). So A -> B becomes 0.1 + 0.2 = 0.3
    new_matrix = new_net.matrix
    assert isinstance(new_matrix, list)
    row0 = new_matrix[0]
    assert isinstance(row0, list)
    assert row0[0] == 0.7
    assert math.isclose(row0[1], 0.3, rel_tol=1e-5)


def test_run_nomikai_sparse() -> None:
    """Test nomikai simulator on sparse matrix."""
    s1 = Stakeholder(name="A", initial_support=0.2, stubbornness=0.9)
    s2 = Stakeholder(name="B", initial_support=0.2, stubbornness=0.9)
    entries = [
        SparseMatrixEntry(row=0, col=0, val=0.9),
        SparseMatrixEntry(row=0, col=1, val=0.1),
        SparseMatrixEntry(row=1, col=0, val=0.1),
        SparseMatrixEntry(row=1, col=1, val=0.9),
    ]
    network = InfluenceNetwork(stakeholders=[s1, s2], matrix=entries)

    settings = NemawashiConfig()
    settings.nomikai_boost = 0.5
    settings.nomikai_reduction = 0.2
    simulator = NomikaiSimulator(settings=settings)

    new_net = simulator.run_nomikai(network, "A")
    assert math.isclose(new_net.stakeholders[0].initial_support, 0.6, rel_tol=1e-5)

    new_entries = new_net.matrix
    assert isinstance(new_entries, list)
    entry_0_0 = next(
        e for e in new_entries if isinstance(e, SparseMatrixEntry) and e.row == 0 and e.col == 0
    )
    entry_0_1 = next(
        e for e in new_entries if isinstance(e, SparseMatrixEntry) and e.row == 0 and e.col == 1
    )
    assert isinstance(entry_0_0, SparseMatrixEntry)
    assert isinstance(entry_0_1, SparseMatrixEntry)
    assert entry_0_0.val == 0.7
    assert math.isclose(entry_0_1.val, 0.3, rel_tol=1e-5)


def test_nemawashi_engine_delegation() -> None:
    """Test that NemawashiEngine properly delegates methods."""
    s1 = Stakeholder(name="A", initial_support=0.5, stubbornness=0.5)
    s2 = Stakeholder(name="B", initial_support=0.5, stubbornness=0.5)
    matrix = [[0.8, 0.2], [0.1, 0.9]]
    network = InfluenceNetwork(stakeholders=[s1, s2], matrix=matrix)

    engine = NemawashiEngine()

    assert engine.identify_influencers(network) == ["B", "A"]
    assert engine._is_connected(matrix) is True

    new_net = engine.run_nomikai(network, "A")
    assert new_net.stakeholders[0].initial_support > 0.5

    ops = engine.calculate_consensus(network)
    assert len(ops) == 2


def test_nemawashi_utils_stochasticity_bad_dense() -> None:
    with pytest.raises(ValidationError):
        NemawashiUtils.validate_stochasticity([[0.5, 0.4]])


def test_nemawashi_utils_stochasticity_bad_sparse() -> None:
    from scipy.sparse import csr_matrix

    bad = csr_matrix([[0.5, 0.4]])
    with pytest.raises(ValidationError):
        NemawashiUtils.validate_stochasticity(bad)


def test_identify_influencers_bad_matrix() -> None:
    s1 = Stakeholder(name="A", initial_support=0.5, stubbornness=0.5)
    s2 = Stakeholder(name="B", initial_support=0.5, stubbornness=0.5)
    # Give matrix nan
    matrix = [[1.0, 0.2], [0.1, 0.9]]  # Valid values, mock dense matrix return later
    # Temporarily disable validation to test dense calculation failure
    with (
        patch(
            "src.domain_models.politics.InfluenceNetwork.validate_stochasticity", return_value=None
        ),
        patch(
            "src.domain_models.politics.InfluenceNetwork.validate_matrix_values",
            return_value=matrix,
        ),
        patch("src.core.nemawashi.utils.NemawashiUtils.validate_stochasticity"),
    ):
        # Constructing InfluenceNetwork directly skips some validators if mocked
        network = InfluenceNetwork(stakeholders=[s1, s2], matrix=[[0.8, 0.2], [0.1, 0.9]])
        network.matrix = [[np.nan, 0.2], [0.1, 0.9]]
        analyzer = InfluenceAnalyzer()
        with pytest.raises(CalculationError):
            analyzer.identify_influencers(network)
