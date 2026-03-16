import logging
import typing

import numpy as np
from typing import Any
from scipy.sparse import coo_matrix, csgraph, csr_matrix
from scipy.sparse.linalg import eigs

from src.core.exceptions import CalculationError, ValidationError
from src.core.nemawashi.utils import NemawashiUtils
from src.domain_models.politics import (
    DenseInfluenceNetwork,
    InfluenceNetwork,
    SparseMatrixEntry,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Analyzes the structure and key influencers of the network.
    """

    def identify_influencers(self, network: InfluenceNetwork) -> list[str]:
        """
        Identify key influencers based on eigenvector centrality.
        Always uses sparse matrices for efficiency and scalability.
        """
        n = len(network.stakeholders)
        if n == 0:
            return []

        try:
            if isinstance(network, DenseInfluenceNetwork):
                # Dense matrix
                matrix_dense = network.matrix
                # Convert to numpy array and validate
                matrix_np = np.array(matrix_dense)
                if not np.all(np.isfinite(matrix_np)):
                    msg = "Influence matrix contains NaN or Inf values."
                    raise ValidationError(msg)  # noqa: TRY301
                NemawashiUtils.validate_stochasticity(matrix_dense, expected_nodes=n)

                # Convert to sparse for efficiency
                centrality = self._eigen_centrality_sparse(csr_matrix(matrix_np))
            else:
                # Sparse matrix
                entries = network.matrix
                centrality = self._eigen_centrality_sparse_entries(entries, n)

            # Rank stakeholders
            indices = np.argsort(centrality)[::-1]  # Descending

            # Map indices back to names
            return [network.stakeholders[i].name for i in indices if i < len(network.stakeholders)]

        except Exception as e:
            msg = "Eigenvector calculation failed"
            logger.exception(msg)
            error_msg = f"{msg}: {e}"
            raise CalculationError(error_msg) from e

    def _eigen_centrality_sparse(self, sparse_mat: csr_matrix) -> np.ndarray[Any, Any]:
        """Compute centrality from pre-built CSR matrix."""
        mat_t = sparse_mat.T
        try:
            vals, vecs = eigs(mat_t, k=1, which="LM")
            centrality = np.abs(vecs.flatten())
            s = np.sum(centrality)
            if s > 0:
                centrality = centrality / s
            return typing.cast(np.ndarray[Any, Any], centrality)
        except Exception as e:
            logger.warning(f"Sparse eig failed, falling back? {e}")
            msg = "Sparse eigen calculation failed"
            raise CalculationError(msg) from e

    def _eigen_centrality_sparse_entries(
        self, entries: list[SparseMatrixEntry], n: int
    ) -> np.ndarray[Any, Any]:
        """
        Compute eigenvector centrality from sparse entries.
        """
        if not entries:
            return np.zeros(n)

        # Build sparse matrix
        rows = [e.row for e in entries]
        cols = [e.col for e in entries]
        data = [e.val for e in entries]

        sparse_mat = coo_matrix((data, (rows, cols)), shape=(n, n), dtype=float).tocsr()

        # Validate stochasticity on the built matrix
        NemawashiUtils.validate_stochasticity(sparse_mat, expected_nodes=n)

        return self._eigen_centrality_sparse(sparse_mat)

    def is_connected(self, matrix_list: list[list[float]]) -> bool:
        """Check if graph has a single component (weakly connected)."""
        if not matrix_list:
            return False

        adj = np.array(matrix_list) > 0
        n_components, _ = csgraph.connected_components(adj, connection="weak")
        return int(n_components) == 1
