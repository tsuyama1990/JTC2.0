import logging
import typing

import numpy as np
from scipy.sparse import csr_matrix

from src.core.config import NemawashiConfig, get_settings
from src.core.exceptions import ValidationError
from src.domain_models.politics import InfluenceNetwork

logger = logging.getLogger(__name__)


class ConsensusEngine:
    """
    Handles the core mathematical consensus building (French-DeGroot Model).
    """

    def __init__(self, settings: NemawashiConfig | None = None) -> None:
        self.settings = settings or get_settings().nemawashi

    def calculate_consensus(self, network: InfluenceNetwork) -> list[float]:
        """
        Run the DeGroot model to calculate final opinion distribution.
        Optimized for memory:
        - Detects dense vs sparse input automatically.
        - Uses sparse matrices (CSR) for large networks or sparse input.
        - Validates row stochasticity efficiently.
        """
        n = len(network.stakeholders)
        if n == 0:
            return []

        opinions = np.array([s.initial_support for s in network.stakeholders])

        # Optimization Threshold for dense input conversion
        DENSE_THRESHOLD = 1000

        try:
            # Check input format
            is_dense_input = False
            if network.matrix and isinstance(network.matrix[0], list):
                is_dense_input = True

            if is_dense_input:
                if n < DENSE_THRESHOLD:
                    # Small dense matrix: use numpy directly
                    matrix_op = np.array(network.matrix)
                else:
                    # Large dense matrix: convert to sparse immediately
                    # Note: This still loads the list of lists into memory if not careful,
                    # but if it's already in the domain model, it's already in memory.
                    # The optimization is for the matrix multiplication loop.
                    matrix_op = csr_matrix(network.matrix)
            else:
                # Sparse input (list of SparseMatrixEntry objects)
                # Construct COO matrix then convert to CSR
                # Using generators for memory efficiency during extraction
                rows = [e.row for e in network.matrix] # type: ignore
                cols = [e.col for e in network.matrix] # type: ignore
                data = [e.val for e in network.matrix] # type: ignore

                matrix_op = csr_matrix((data, (rows, cols)), shape=(n, n))

            # Validate Stochasticity
            # Calculate row sums efficiently
            if isinstance(matrix_op, np.ndarray):
                row_sums = matrix_op.sum(axis=1)
            else:
                # For sparse matrix, sum returns matrix object
                row_sums = np.array(matrix_op.sum(axis=1)).flatten()

            if not np.allclose(row_sums, 1.0, atol=1e-5):
                 # Log detailed error for debugging
                 logger.error(f"Matrix row sums invalid: {row_sums[:5]}...")
                 raise ValidationError("Influence matrix rows must sum to 1.0")

        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            logger.exception("Matrix processing error")
            raise ValidationError(f"Failed to process matrix: {e}") from e

        max_steps = self.settings.max_steps
        tolerance = self.settings.tolerance

        current_ops = opinions

        for _ in range(max_steps):
            # Matrix-Vector Multiplication
            # Works for both dense (numpy) and sparse (scipy)
            next_ops = matrix_op.dot(current_ops)

            if np.allclose(current_ops, next_ops, atol=tolerance):
                logger.info("Consensus converged.")
                return typing.cast(list[float], next_ops.tolist())
            current_ops = next_ops

        return typing.cast(list[float], current_ops.tolist())
