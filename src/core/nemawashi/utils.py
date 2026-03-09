from typing import cast

import numpy as np
from scipy.sparse import coo_matrix, csr_matrix

from src.core.exceptions import ValidationError
from src.domain_models.politics import InfluenceNetwork, SparseMatrixEntry


class NemawashiUtils:
    """Shared utility functions for Nemawashi calculations."""

    @staticmethod
    def validate_stochasticity(
        matrix: csr_matrix | list[list[float]], tolerance: float = 1e-6
    ) -> None:
        """
        Validate that matrix rows sum to approximately 1.0 and bounds are [0,1].
        Supports both sparse (csr_matrix) and dense (list[list[float]]) inputs.
        """
        try:
            if hasattr(matrix, "sum"):
                # Sparse or numpy matrix
                shape = getattr(matrix, "shape", (0, 0))
                if shape[0] > 10000 or shape[1] > 10000:
                    msg = f"Matrix dimensions {shape} exceed maximum allowed size of 10000x10000"
                    raise ValueError(msg)

                row_sums = matrix.sum(axis=1)
                # Convert to 1D array
                row_sums = row_sums.A1 if hasattr(row_sums, "A1") else np.array(row_sums).flatten()

                # Retrieve actual values for bounds checking
                values = matrix.data if hasattr(matrix, "data") else np.asarray(matrix).flatten()
            else:
                # List of lists
                dense = cast(list[list[float]], matrix)
                if len(dense) > 10000 or (len(dense) > 0 and len(dense[0]) > 10000):
                    msg = "Matrix dimensions exceed maximum allowed size of 10000x10000"
                    raise ValueError(msg)

                # For very large lists, iterative row checking is safer than creating a giant numpy array
                if len(dense) > 1000:
                    for row in dense:
                        if not all(0.0 - tolerance <= val <= 1.0 + tolerance for val in row):
                            msg_bounds = "Influence matrix entries must be within bounds [0, 1]."
                            raise ValidationError(msg_bounds)
                        if not np.isclose(sum(row), 1.0, rtol=tolerance, atol=tolerance):
                            msg_sum = "Influence matrix rows must precisely sum to 1.0"
                            raise ValidationError(msg_sum)
                    return  # Successfully validated large list line by line

                row_sums = np.array([sum(row) for row in dense])
                values = np.array(dense).flatten()
        except Exception as e:
            msg = f"Stochasticity check failed during summation: {e}"
            raise ValidationError(msg) from e

        if not np.all(np.isfinite(values)):
            msg = "Influence matrix contains NaN or Inf values."
            raise ValidationError(msg)

        if np.any((values < -tolerance) | (values > 1.0 + tolerance)):
            msg = "Influence matrix entries must be within bounds [0, 1]."
            raise ValidationError(msg)

        if not np.allclose(row_sums, 1.0, rtol=tolerance, atol=tolerance):
            msg = "Influence matrix rows must precisely sum to 1.0"
            raise ValidationError(msg)

    @staticmethod
    def build_sparse_matrix(network: InfluenceNetwork, n: int) -> csr_matrix:
        """
        Construct a CSR matrix from the network data efficiently.
        Handles both dense and sparse input formats.
        """
        if n > 10000:
            msg = f"Network size {n} exceeds limit of 10,000 stakeholders."
            raise ValueError(msg)

        if not network.matrix:
            return csr_matrix((n, n), dtype=float)

        if isinstance(network.matrix[0], list):
            try:
                return csr_matrix(network.matrix, shape=(n, n), dtype=float)
            except Exception as e:
                msg = f"Failed to convert dense matrix: {e}"
                raise ValidationError(msg) from e

        # Sparse input
        entries = cast(list[SparseMatrixEntry], network.matrix)
        count = len(entries)

        try:
            rows = np.fromiter((e.row for e in entries), dtype=int, count=count)
            cols = np.fromiter((e.col for e in entries), dtype=int, count=count)
            data = np.fromiter((e.val for e in entries), dtype=float, count=count)

            return coo_matrix((data, (rows, cols)), shape=(n, n), dtype=float).tocsr()
        except Exception as e:
            msg = f"Failed to build sparse matrix: {e}"
            raise ValidationError(msg) from e
