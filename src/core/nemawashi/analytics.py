import logging
import typing
from typing import cast

import numpy as np
from scipy.sparse import coo_matrix, csgraph, csr_matrix
from scipy.sparse.linalg import eigs

from src.core.exceptions import CalculationError, ValidationError
from src.core.nemawashi.utils import NemawashiUtils
from src.domain_models.politics import InfluenceNetwork, SparseMatrixEntry

logger = logging.getLogger(__name__)


class InfluenceAnalyzer:
    """
    Analyzes the structure and key influencers of the network.
    """

    def identify_influencers(self, network: InfluenceNetwork) -> list[str]:
        """
        Identify key influencers based on eigenvector centrality.
        Uses sparse matrices for efficiency if the network is large (>1000 nodes).
        """
        n = len(network.stakeholders)
        if n == 0:
            return []

        try:
            # Check if dense
            if network.matrix and isinstance(network.matrix[0], list):
                # Dense matrix (list of lists)
                matrix_dense = cast(list[list[float]], network.matrix)
                # Validation
                NemawashiUtils.validate_stochasticity(matrix_dense)

                # Check size to decide strategy
                if n > 1000:
                     # Convert to sparse for efficiency
                     centrality = self._eigen_centrality_sparse(csr_matrix(matrix_dense))
                else:
                     centrality = self._eigen_centrality_dense(matrix_dense)
            else:
                # Sparse matrix (list of entries) or empty
                entries = cast(list[SparseMatrixEntry], network.matrix)
                # Validation (Dimensions checked, stochasticity check harder on raw entries without building matrix)
                # We build matrix first then validate

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

    def _eigen_centrality_dense(self, matrix_list: list[list[float]]) -> np.ndarray:
        """
        Compute eigenvector centrality using dense numpy arrays.
        Safe for small networks.
        """
        matrix = np.array(matrix_list)

        if not np.all(np.isfinite(matrix)):
            msg = "Influence matrix contains NaN or Inf values."
            raise ValidationError(msg)

        # Eig on transpose for left eigenvectors
        eigenvalues, eigenvectors = np.linalg.eig(matrix.T)

        # Find eigenvalue closest to 1.0
        idx = np.argmin(np.abs(eigenvalues - 1.0))
        centrality = np.abs(eigenvectors[:, idx])

        # Normalize
        s = np.sum(centrality)
        if s > 0:
            centrality = centrality / s

        return typing.cast(np.ndarray, centrality)

    def _eigen_centrality_sparse(self, sparse_mat: csr_matrix) -> np.ndarray:
        """Compute centrality from pre-built CSR matrix."""
        mat_t = sparse_mat.T
        try:
            vals, vecs = eigs(mat_t, k=1, which='LM')
            centrality = np.abs(vecs.flatten())
            s = np.sum(centrality)
            if s > 0:
                centrality = centrality / s
            return typing.cast(np.ndarray, centrality)
        except Exception as e:
             logger.warning(f"Sparse eig failed, falling back? {e}")
             msg = "Sparse eigen calculation failed"
             raise CalculationError(msg) from e

    def _eigen_centrality_sparse_entries(self, entries: list[SparseMatrixEntry], n: int) -> np.ndarray:
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
        NemawashiUtils.validate_stochasticity(sparse_mat)

        return self._eigen_centrality_sparse(sparse_mat)

    def is_connected(self, matrix_list: list[list[float]]) -> bool:
        """Check if graph has a single component (weakly connected)."""
        if not matrix_list:
            return False

        adj = np.array(matrix_list) > 0
        n_components, _ = csgraph.connected_components(adj, connection="weak")
        return int(n_components) == 1
