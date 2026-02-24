from typing import cast

import numpy as np
from scipy.sparse import spmatrix

from src.core.exceptions import ValidationError
from src.domain_models.politics import SparseMatrixEntry


class NemawashiUtils:
    """Shared utility functions for Nemawashi calculations."""

    @staticmethod
    def validate_stochasticity(matrix: spmatrix | list[list[float]], tolerance: float = 1e-6) -> None:
        """
        Validate that matrix rows sum to approximately 1.0.
        Supports both sparse (spmatrix) and dense (list[list[float]]) inputs.
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
    def validate_dimensions(matrix: list[list[float]] | list[SparseMatrixEntry], n: int) -> None:
        """
        Validate matrix dimensions against stakeholder count n.
        """
        if isinstance(matrix, list) and matrix and isinstance(matrix[0], list):
            # Dense
            if len(matrix) != n:
                raise ValidationError(f"Matrix rows {len(matrix)} != stakeholders {n}")
            for row in matrix:
                if isinstance(row, list) and len(row) != n:
                    raise ValidationError("Matrix is not square")
        elif isinstance(matrix, list):
            # Sparse entries
            for entry in matrix:
                if isinstance(entry, SparseMatrixEntry):
                    if not (0 <= entry.row < n) or not (0 <= entry.col < n):
                         raise ValidationError(f"Sparse entry out of bounds: {entry}")
