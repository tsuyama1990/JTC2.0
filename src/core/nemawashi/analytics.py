import logging
import typing

import numpy as np
from scipy.sparse import csgraph, csr_matrix
from scipy.sparse.linalg import eigs

from src.core.exceptions import CalculationError, ValidationError
from src.domain_models.politics import InfluenceNetwork

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
        n = len(network.matrix)
        if n == 0:
            return []

        # Heuristic threshold for sparse mode
        use_sparse = n > 1000

        try:
            if use_sparse:
                centrality = self._eigen_centrality_sparse(network.matrix)
            else:
                centrality = self._eigen_centrality_dense(network.matrix)

            # Rank stakeholders
            indices = np.argsort(centrality)[::-1]  # Descending
            return [network.stakeholders[i].name for i in indices]

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

    def _eigen_centrality_sparse(self, matrix_list: list[list[float]]) -> np.ndarray:
        """
        Compute eigenvector centrality using sparse matrices.
        Efficient for large, sparse networks.
        """
        # Convert to CSR (Compressed Sparse Row)
        # Note: This still requires creating the CSR from list, which iterates it.
        # Ideally, we would construct from (data, indices, indptr) but list[list] is given.
        sparse_mat = csr_matrix(matrix_list)

        # Transpose for left eigenvector
        mat_t = sparse_mat.T

        # Calculate 1 eigenvector with eigenvalue close to 1
        # 'LM' = Largest Magnitude.
        # Since it's stochastic, max eigenvalue is 1.
        vals, vecs = eigs(mat_t, k=1, which='LM')

        # eigs returns complex, take real part of abs
        centrality = np.abs(vecs.flatten())

        # Normalize
        s = np.sum(centrality)
        if s > 0:
            centrality = centrality / s

        return typing.cast(np.ndarray, centrality)

    def is_connected(self, matrix_list: list[list[float]]) -> bool:
        """Check if graph has a single component (weakly connected)."""
        if not matrix_list:
            return False

        adj = np.array(matrix_list) > 0
        n_components, _ = csgraph.connected_components(adj, connection="weak")
        return int(n_components) == 1
