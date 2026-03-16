from typing import Any
from unittest.mock import patch

import pytest
from scipy.sparse import csr_matrix

from src.core.config import get_settings
from src.core.exceptions import ValidationError
from src.core.nemawashi.consensus import ConsensusService
from src.core.nemawashi.nomikai import SimulationService
from src.core.nemawashi.utils import NemawashiUtils
from src.domain_models.politics import (
    DenseInfluenceNetwork,
    SparseInfluenceNetwork,
    SparseMatrixEntry,
    Stakeholder,
)


@pytest.fixture
def base_sparse_network() -> SparseInfluenceNetwork:
    s1 = Stakeholder(name="A", initial_support=0.5, stubbornness=0.5)
    return SparseInfluenceNetwork(
        stakeholders=[s1], matrix=[SparseMatrixEntry(row=0, col=0, val=1.0)]
    )


@pytest.fixture
def base_dense_network() -> DenseInfluenceNetwork:
    s1 = Stakeholder(name="A", initial_support=0.5, stubbornness=0.5)
    return DenseInfluenceNetwork(stakeholders=[s1], matrix=[[1.0]])


def test_consensus_conversion_failure(base_sparse_network: SparseInfluenceNetwork) -> None:
    """Test that matrix conversion failures are handled gracefully."""
    engine = ConsensusService()

    with (
        patch("src.core.nemawashi.utils.coo_matrix", side_effect=Exception("Conversion Boom")),
        pytest.raises(ValidationError, match="Failed to build sparse matrix"),
    ):
        engine.calculate_consensus(base_sparse_network)


def test_consensus_dense_conversion_failure(base_dense_network: DenseInfluenceNetwork) -> None:
    """Test dense matrix conversion failure."""
    engine = ConsensusService()

    with (
        patch("src.core.nemawashi.utils.csr_matrix", side_effect=Exception("Dense Boom")),
        pytest.raises(ValidationError, match="Failed to convert dense matrix"),
    ):
        engine.calculate_consensus(base_dense_network)


INVALID_STOCHASTIC_SUM = 0.9


def test_consensus_stochasticity_check_failure(base_dense_network: DenseInfluenceNetwork) -> None:
    """Test that runtime stochasticity check catches invalid matrices."""
    engine = ConsensusService()

    bad_matrix = csr_matrix([[INVALID_STOCHASTIC_SUM]])  # Sum is 0.9

    with patch(
        "src.core.nemawashi.consensus.NemawashiUtils.build_sparse_matrix",
        return_value=bad_matrix,
    ):
        result = engine.calculate_consensus(base_dense_network)
        assert len(result) == 1
        assert pytest.approx(result[0]) == 0.5


def test_consensus_calculation() -> None:
    """Test standard calculation flow."""
    s1 = Stakeholder(name="A", initial_support=0.0, stubbornness=0.0)
    s2 = Stakeholder(name="B", initial_support=1.0, stubbornness=1.0)
    # A follows B (100%), B follows self (100%)
    entries = [SparseMatrixEntry(row=0, col=1, val=1.0), SparseMatrixEntry(row=1, col=1, val=1.0)]
    network = SparseInfluenceNetwork(stakeholders=[s1, s2], matrix=entries)

    engine = ConsensusService()
    result = engine.calculate_consensus(network)

    assert result[0] > 0.9  # A should converge to B
    assert result[1] == 1.0


def test_run_nomikai_invalid_target(base_dense_network: DenseInfluenceNetwork) -> None:
    service = SimulationService()
    with pytest.raises(ValidationError, match="Target name must be a non-empty string."):
        service.run_nomikai(base_dense_network, "")


def test_run_nomikai_target_not_found(base_dense_network: DenseInfluenceNetwork) -> None:
    service = SimulationService()
    with pytest.raises(ValidationError, match="Target B not found."):
        service.run_nomikai(base_dense_network, "B")


MAX_STAKEHOLDERS = 10001


def test_run_nomikai_exceeds_limit() -> None:
    service = SimulationService()
    stakeholders = [
        Stakeholder(name=f"A{i}", initial_support=0.5, stubbornness=0.5)
        for i in range(MAX_STAKEHOLDERS)
    ]
    net = SparseInfluenceNetwork(
        stakeholders=stakeholders,
        matrix=[SparseMatrixEntry(row=i, col=i, val=1.0) for i in range(MAX_STAKEHOLDERS)],
    )
    with pytest.raises(ValidationError, match="exceeds limit"):
        service.run_nomikai(net, "A0")


@pytest.fixture
def sim_service() -> SimulationService:
    service = SimulationService()
    service.settings.nomikai_reduction = 0.1
    service.settings.nomikai_boost = 0.2
    return service


@pytest.fixture
def dense_network_nomikai() -> DenseInfluenceNetwork:
    return DenseInfluenceNetwork(
        stakeholders=[
            Stakeholder(name="A", initial_support=0.5, stubbornness=0.8),
            Stakeholder(name="B", initial_support=0.3, stubbornness=0.9),
        ],
        matrix=[[0.8, 0.2], [0.1, 0.9]],
    )


@pytest.fixture
def sparse_network_nomikai() -> SparseInfluenceNetwork:
    return SparseInfluenceNetwork(
        stakeholders=[
            Stakeholder(name="A", initial_support=0.5, stubbornness=0.8),
            Stakeholder(name="B", initial_support=0.3, stubbornness=0.9),
        ],
        matrix=[
            SparseMatrixEntry(row=0, col=0, val=0.8),
            SparseMatrixEntry(row=0, col=1, val=0.2),
            SparseMatrixEntry(row=1, col=1, val=1.0),
        ],
    )


def test_run_nomikai_dense_success(
    sim_service: SimulationService, dense_network_nomikai: DenseInfluenceNetwork
) -> None:
    new_net = sim_service.run_nomikai(dense_network_nomikai, "A")
    assert new_net.stakeholders[0].initial_support == 0.5 + 0.5 * 0.2
    assert abs(new_net.matrix[0][0] - 0.7) < 1e-9  # type: ignore
    assert abs(new_net.matrix[0][1] - 0.3) < 1e-9  # type: ignore


def test_run_nomikai_dense_reduction_exceeds(
    sim_service: SimulationService, dense_network_nomikai: DenseInfluenceNetwork
) -> None:
    sim_service.settings.nomikai_reduction = 0.9
    with pytest.raises(ValidationError, match="exceeds current self-weight"):
        sim_service.run_nomikai(dense_network_nomikai, "A")


def test_run_nomikai_sparse_success(
    sim_service: SimulationService, sparse_network_nomikai: SparseInfluenceNetwork
) -> None:
    new_net = sim_service.run_nomikai(sparse_network_nomikai, "A")
    assert new_net.stakeholders[0].initial_support == 0.5 + 0.5 * 0.2
    assert abs(next(e.val for e in new_net.matrix if e.row == 0 and e.col == 0) - 0.7) < 1e-9  # type: ignore
    assert abs(next(e.val for e in new_net.matrix if e.row == 0 and e.col == 1) - 0.3) < 1e-9  # type: ignore


def test_run_nomikai_sparse_reduction_exceeds(
    sim_service: SimulationService, sparse_network_nomikai: SparseInfluenceNetwork
) -> None:
    sim_service.settings.nomikai_reduction = 0.9
    with pytest.raises(ValidationError, match="exceeds current self-weight"):
        sim_service.run_nomikai(sparse_network_nomikai, "A")


def test_run_nomikai_sparse_no_outgoing(sim_service: SimulationService) -> None:
    net = SparseInfluenceNetwork(
        stakeholders=[
            Stakeholder(name="A", initial_support=0.5, stubbornness=0.8),
            Stakeholder(name="B", initial_support=0.3, stubbornness=0.9),
        ],
        matrix=[SparseMatrixEntry(row=0, col=0, val=1.0), SparseMatrixEntry(row=1, col=1, val=1.0)],
    )
    new_net = sim_service.run_nomikai(net, "A")
    # No other outgoing edges, so self_entry shouldn't change
    assert next(e.val for e in new_net.matrix if e.row == 0 and e.col == 0) == 1.0  # type: ignore


def test_run_nomikai_sparse_no_self(sim_service: SimulationService) -> None:
    net = SparseInfluenceNetwork(
        stakeholders=[
            Stakeholder(name="A", initial_support=0.5, stubbornness=0.8),
            Stakeholder(name="B", initial_support=0.3, stubbornness=0.9),
        ],
        matrix=[SparseMatrixEntry(row=0, col=1, val=1.0), SparseMatrixEntry(row=1, col=1, val=1.0)],
    )
    new_net = sim_service.run_nomikai(net, "A")
    assert new_net.stakeholders[0].stubbornness == 1.0


import numpy as np


def test_validate_stochasticity_csr_success() -> None:
    mat = csr_matrix([[0.5, 0.5], [0.2, 0.8]])
    NemawashiUtils.validate_stochasticity(mat, expected_nodes=2)


def test_validate_stochasticity_csr_dim_mismatch() -> None:
    mat = csr_matrix([[0.5, 0.5], [0.2, 0.8]])
    with pytest.raises(ValidationError, match="do not match expected nodes"):
        NemawashiUtils.validate_stochasticity(mat, expected_nodes=3)


def test_validate_stochasticity_csr_nan() -> None:
    mat = csr_matrix([[np.nan, 0.5], [0.2, 0.8]])
    with pytest.raises(ValidationError, match="NaN or Inf"):
        NemawashiUtils.validate_stochasticity(mat, expected_nodes=2)


INVALID_BOUNDS_VALUES = (1.5, -0.5)


def test_validate_stochasticity_csr_bounds() -> None:
    mat = csr_matrix([[INVALID_BOUNDS_VALUES[0], INVALID_BOUNDS_VALUES[1]], [0.2, 0.8]])
    with pytest.raises(ValidationError, match="between 0.0 and 1.0"):
        NemawashiUtils.validate_stochasticity(mat, expected_nodes=2)


def test_validate_stochasticity_ndarray_success() -> None:
    mat = np.array([[0.5, 0.5], [0.2, 0.8]])
    NemawashiUtils.validate_stochasticity(mat, expected_nodes=2)


def test_validate_stochasticity_ndarray_not_square() -> None:
    mat = np.array([[0.5, 0.5, 0.0], [0.2, 0.8, 0.0]])
    with pytest.raises(ValidationError, match="must be square"):
        NemawashiUtils.validate_stochasticity(mat)


def test_validate_stochasticity_ndarray_dim_mismatch() -> None:
    mat = np.array([[0.5, 0.5], [0.2, 0.8]])
    with pytest.raises(ValidationError, match="do not match expected nodes"):
        NemawashiUtils.validate_stochasticity(mat, expected_nodes=3)


def test_validate_stochasticity_ndarray_nan() -> None:
    mat = np.array([[np.nan, 0.5], [0.2, 0.8]])
    with pytest.raises(ValidationError, match="NaN or Inf"):
        NemawashiUtils.validate_stochasticity(mat)


def test_validate_stochasticity_ndarray_bounds() -> None:
    mat = np.array([[INVALID_BOUNDS_VALUES[0], INVALID_BOUNDS_VALUES[1]], [0.2, 0.8]])
    with pytest.raises(ValidationError, match="between 0.0 and 1.0"):
        NemawashiUtils.validate_stochasticity(mat)


def test_validate_stochasticity_list_success() -> None:
    mat = [[0.5, 0.5], [0.2, 0.8]]
    NemawashiUtils.validate_stochasticity(mat, expected_nodes=2)


def test_validate_stochasticity_list_dim_mismatch() -> None:
    mat = [[0.5, 0.5], [0.2, 0.8]]
    with pytest.raises(ValidationError, match="do not match expected nodes"):
        NemawashiUtils.validate_stochasticity(mat, expected_nodes=3)


def test_validate_stochasticity_list_not_square() -> None:
    mat = [[0.5, 0.5, 0.0], [0.2, 0.8]]
    with pytest.raises(ValidationError, match="must be square"):
        NemawashiUtils.validate_stochasticity(mat)


def test_validate_stochasticity_list_nan() -> None:
    mat = [[float("nan"), 0.5], [0.2, 0.8]]
    with pytest.raises(ValidationError, match="NaN or Inf"):
        NemawashiUtils.validate_stochasticity(mat)


def test_validate_stochasticity_list_bounds() -> None:
    mat = [[INVALID_BOUNDS_VALUES[0], INVALID_BOUNDS_VALUES[1]], [0.2, 0.8]]
    with pytest.raises(ValidationError, match="between 0.0 and 1.0"):
        NemawashiUtils.validate_stochasticity(mat)


def test_validate_stochasticity_list_fails_sum() -> None:
    mat = [[0.5, 0.4], [0.2, 0.8]]
    with pytest.raises(ValidationError, match="must sum to 1.0"):
        NemawashiUtils.validate_stochasticity(mat)


class MockNetwork:
    def __init__(self, matrix: Any, is_dense: bool) -> None:
        self.matrix = matrix
        self.is_dense = is_dense


MAX_STAKEHOLDERS_FOR_TEST = 10


def test_build_sparse_matrix_exceeds_max() -> None:

    get_settings.cache_clear()
    settings = get_settings()
    settings.nemawashi.max_stakeholders = MAX_STAKEHOLDERS_FOR_TEST
    net = MockNetwork([], False)
    with pytest.raises(ValueError, match="exceeds limit"):
        NemawashiUtils.build_sparse_matrix(net, 11)


def test_build_sparse_matrix_empty() -> None:

    get_settings.cache_clear()
    net = MockNetwork([], False)
    mat = NemawashiUtils.build_sparse_matrix(net, 2)
    assert isinstance(mat, csr_matrix)
    assert mat.shape == (2, 2)


def test_build_sparse_matrix_dense() -> None:
    net = MockNetwork([[0.5, 0.5], [0.5, 0.5]], True)
    mat = NemawashiUtils.build_sparse_matrix(net, 2)
    assert isinstance(mat, csr_matrix)
    assert mat.shape == (2, 2)
    assert mat[0, 0] == 0.5


def test_build_sparse_matrix_dense_fail() -> None:
    net = MockNetwork([0.5, 0.5], True)
    with pytest.raises(ValidationError, match="Failed to convert dense matrix"):
        NemawashiUtils.build_sparse_matrix(net, 2)


def test_build_sparse_matrix_sparse_success() -> None:
    net = MockNetwork([SparseMatrixEntry(row=0, col=1, val=0.5)], False)
    mat = NemawashiUtils.build_sparse_matrix(net, 2)
    assert isinstance(mat, csr_matrix)
    assert mat[0, 1] == 0.5


def test_build_sparse_matrix_sparse_invalid_type() -> None:
    net = MockNetwork([{"row": 0, "col": 1, "val": 0.5}], False)
    with pytest.raises(ValidationError, match="Invalid sparse entry structure"):
        NemawashiUtils.build_sparse_matrix(net, 2)


def test_build_sparse_matrix_sparse_out_of_bounds() -> None:
    net = MockNetwork([SparseMatrixEntry(row=0, col=3, val=0.5)], False)
    with pytest.raises(ValidationError, match="out of bounds"):
        NemawashiUtils.build_sparse_matrix(net, 2)
