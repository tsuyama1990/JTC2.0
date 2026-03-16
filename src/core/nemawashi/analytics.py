import logging
import typing

import numpy as np
import numpy.typing as npt
from scipy.linalg import LinAlgError
from scipy.sparse import coo_matrix, csgraph, csr_matrix
from scipy.sparse.linalg import eigs

from src.core.exceptions import CalculationError, ValidationError
from src.core.nemawashi.utils import NemawashiUtils
from src.domain_models.politics import (
    DenseInfluenceNetwork,
    SparseInfluenceNetwork,
    SparseMatrixEntry,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Analyzes the structure and key influencers of the network.
    """

    def identify_influencers(
        self, network: DenseInfluenceNetwork | SparseInfluenceNetwork
    ) -> list[str]:
        """
        Identify key influencers based on eigenvector centrality.
        Always uses sparse matrices for efficiency and scalability.
        """
        if not network.stakeholders:
            return []

        n = len(network.stakeholders)

        try:
            if network.is_dense:
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
                if not isinstance(entries, list):
                    msg = "Expected sparse matrix entries to be a list"
                    raise TypeError(msg)  # noqa: TRY301
                if len(entries) > 0 and not isinstance(entries[0], SparseMatrixEntry):
                    msg = "Expected list elements to be SparseMatrixEntry"
                    raise TypeError(msg)  # noqa: TRY301
                centrality = self._eigen_centrality_sparse_entries(
                    typing.cast(list[SparseMatrixEntry], entries), n
                )

            # Rank stakeholders
            indices = np.argsort(centrality)[::-1]  # Descending

            # Map indices back to names
            return [network.stakeholders[i].name for i in indices]

        except (ValueError, TypeError, ValidationError) as e:
            msg = "Eigenvector calculation failed"
            logger.exception(msg)
            error_msg = f"{msg}: {e}"
            raise CalculationError(error_msg) from e

    def _eigen_centrality_sparse(self, sparse_mat: csr_matrix) -> npt.NDArray[np.float64]:
        """Compute centrality from pre-built CSR matrix."""
        mat_t = sparse_mat.T

        try:
            if mat_t.shape[0] == 1:
                centrality = np.array([1.0], dtype=np.float64)
            else:
                vals, vecs = eigs(mat_t, k=1, which="LM")
                centrality = np.abs(vecs.flatten())
        except (LinAlgError, ValueError) as e:
            logger.warning(f"Sparse eig failed: {e}")
            msg = "Sparse eigen calculation failed"
            raise CalculationError(msg) from e
        else:
            s = np.sum(centrality)
            if s > 0:
                centrality = centrality / s
            return centrality

    def _eigen_centrality_sparse_entries(
        self, entries: list[SparseMatrixEntry], n: int
    ) -> npt.NDArray[np.float64]:
        """
        Compute eigenvector centrality from sparse entries.
        """
        # Build sparse matrix
        rows = [e.row for e in entries]
        cols = [e.col for e in entries]
        data = [e.val for e in entries]

        sparse_mat = coo_matrix((data, (rows, cols)), shape=(n, n), dtype=float).tocsr()

        # Validate stochasticity on the built matrix
        NemawashiUtils.validate_stochasticity(sparse_mat, expected_nodes=n)

        return self._eigen_centrality_sparse(sparse_mat)

    def is_connected(self, matrix: csr_matrix) -> bool:
        """Check if graph has a single component (weakly connected)."""
        if matrix.shape[0] == 0:
            return True

        adj = matrix > 0
        n_components, _ = csgraph.connected_components(adj, connection="weak")
        return int(n_components) == 1
