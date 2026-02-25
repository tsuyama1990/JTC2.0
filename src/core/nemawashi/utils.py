from typing import cast

import numpy as np
from scipy.sparse import coo_matrix, csr_matrix

from src.core.exceptions import ValidationError
from src.domain_models.politics import InfluenceNetwork, SparseMatrixEntry


class NemawashiUtils:
    """Shared utility functions for Nemawashi calculations."""

    @staticmethod
    def validate_stochasticity(matrix: csr_matrix | list[list[float]], tolerance: float = 1e-6) -> None:
        """
        Validate that matrix rows sum to approximately 1.0.
        Supports both sparse (csr_matrix) and dense (list[list[float]]) inputs.
        """
        try:
            if hasattr(matrix, "sum"):
                # Sparse or numpy matrix
                row_sums = matrix.sum(axis=1) # type: ignore
                # Convert to 1D array
                if hasattr(row_sums, "A1"):
                    row_sums = row_sums.A1
                else:
                    row_sums = np.array(row_sums).flatten()
            else:
                # List of lists
                dense = cast(list[list[float]], matrix)
                row_sums = np.array([sum(row) for row in dense])

            if not np.allclose(row_sums, 1.0, atol=tolerance):
                 msg = "Influence matrix rows must sum to 1.0"
                 raise ValidationError(msg)

        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            msg = f"Stochasticity check failed: {e}"
            raise ValidationError(msg) from e

    @staticmethod
    def build_sparse_matrix(network: InfluenceNetwork, n: int) -> csr_matrix:
        """
        Construct a CSR matrix from the network data efficiently.
        Handles both dense and sparse input formats.
        """
        if n > 10000:
            raise ValueError(f"Network size {n} exceeds limit of 10,000 stakeholders.")

        if not network.matrix:
            return csr_matrix((n, n), dtype=float)

        if isinstance(network.matrix[0], list):
            try:
                return csr_matrix(network.matrix, shape=(n, n), dtype=float)
            except Exception as e:
                raise ValidationError(f"Failed to convert dense matrix: {e}") from e

        # Sparse input
        entries = cast(list[SparseMatrixEntry], network.matrix)
        count = len(entries)

        try:
            rows = np.fromiter((e.row for e in entries), dtype=int, count=count)
            cols = np.fromiter((e.col for e in entries), dtype=int, count=count)
            data = np.fromiter((e.val for e in entries), dtype=float, count=count)

            return coo_matrix((data, (rows, cols)), shape=(n, n), dtype=float).tocsr()
        except Exception as e:
            raise ValidationError(f"Failed to build sparse matrix: {e}") from e
