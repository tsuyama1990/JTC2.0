from typing import cast

import numpy as np
from scipy.sparse import coo_matrix, csr_matrix

from src.core.exceptions import ValidationError
from src.domain_models.politics import (
    DenseInfluenceNetwork,
    InfluenceNetwork,
)


class NemawashiUtils:
    """Shared utility functions for Nemawashi calculations."""

    @staticmethod
    def validate_stochasticity(
        matrix: csr_matrix | list[list[float]] | np.ndarray,
        tolerance: float = 1e-6,
        expected_nodes: int | None = None,
    ) -> None:
        """
        Validate that matrix rows sum to approximately 1.0.
        Supports both sparse (csr_matrix) and dense (list[list[float]] or ndarray) inputs.
        Also validates that all values are in the range [0.0, 1.0] and checks dimension squareness.
        """
        try:
            if hasattr(matrix, "data") and isinstance(matrix, csr_matrix):
                if expected_nodes and matrix.shape != (expected_nodes, expected_nodes):
                    msg = f"Matrix dimensions {matrix.shape} do not match expected nodes ({expected_nodes}, {expected_nodes})"
                    raise ValidationError(msg)  # noqa: TRY301

                # Check value bounds for sparse matrix
                if (matrix.data < 0.0).any() or (matrix.data > 1.0).any():
                    msg = "Matrix values must be between 0.0 and 1.0"
                    raise ValidationError(msg)  # noqa: TRY301
                row_sums = matrix.sum(axis=1).A1

            elif isinstance(matrix, np.ndarray):
                if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1]:
                    msg = f"Matrix must be square, got shape {matrix.shape}"
                    raise ValidationError(msg)  # noqa: TRY301
                if expected_nodes and matrix.shape != (expected_nodes, expected_nodes):
                    msg = f"Matrix dimensions {matrix.shape} do not match expected nodes ({expected_nodes}, {expected_nodes})"
                    raise ValidationError(msg)  # noqa: TRY301

                if (matrix < 0.0).any() or (matrix > 1.0).any():
                    msg = "Matrix values must be between 0.0 and 1.0"
                    raise ValidationError(msg)  # noqa: TRY301
                row_sums = matrix.sum(axis=1)

            else:
                # List of lists
                dense = cast(list[list[float]], matrix)
                n_rows = len(dense)
                if expected_nodes and n_rows != expected_nodes:
                    msg = f"Matrix rows ({n_rows}) do not match expected nodes ({expected_nodes})"
                    raise ValidationError(msg)  # noqa: TRY301

                for row in dense:
                    if len(row) != n_rows:
                        msg = "Matrix must be square"
                        raise ValidationError(msg)  # noqa: TRY301
                    for val in row:
                        if not (0.0 <= val <= 1.0):
                            msg = "Matrix values must be between 0.0 and 1.0"
                            raise ValidationError(msg)  # noqa: TRY301
                row_sums = np.array([sum(row) for row in dense])
        except ValidationError:
            raise
        except Exception as e:
            msg = f"Stochasticity check failed: {e}"
            raise ValidationError(msg) from e

        failing_indices = np.where(~np.isclose(row_sums, 1.0, atol=tolerance))[0]
        if failing_indices.size > 0:
            details = [f"row {i} sum={row_sums[i]:.4f}" for i in failing_indices[:5]]
            extra = "..." if failing_indices.size > 5 else ""
            msg = f"Influence matrix stochasticity failure (must sum to 1.0): {', '.join(details)} {extra}"
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

        if isinstance(network, DenseInfluenceNetwork):
            try:
                return csr_matrix(network.matrix, shape=(n, n), dtype=float)
            except Exception as e:
                msg = f"Failed to convert dense matrix: {e}"
                raise ValidationError(msg) from e

        # Sparse input
        entries = network.matrix

        # Validate indices
        for entry in entries:
            if not (0 <= entry.row < n) or not (0 <= entry.col < n):
                msg = f"Sparse entry indices out of bounds: row {entry.row}, col {entry.col} for network size {n}"
                raise ValidationError(msg)

        count = len(entries)

        try:
            rows = np.fromiter((e.row for e in entries), dtype=int, count=count)
            cols = np.fromiter((e.col for e in entries), dtype=int, count=count)
            data = np.fromiter((e.val for e in entries), dtype=float, count=count)

            return coo_matrix((data, (rows, cols)), shape=(n, n), dtype=float).tocsr()
        except Exception as e:
            msg = f"Failed to build sparse matrix: {e}"
            raise ValidationError(msg) from e
