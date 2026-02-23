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
        - Small/Medium (<1000 nodes): Convert to dense numpy array once.
        - Large (>1000 nodes): Convert to sparse matrix once.
        - Chunking removed from inner loop as conversion overhead defeats purpose if fitting in RAM.
        - Validation of row sums happens on the optimized structure.
        """
        opinions = np.array([s.initial_support for s in network.stakeholders])
        rows = len(network.matrix)

        # Optimization Threshold
        SPARSE_THRESHOLD = 1000

        try:
            if rows < SPARSE_THRESHOLD:
                # Dense Mode: Efficient for small matrices
                matrix_op = np.array(network.matrix)
                # Validate Stochasticity
                if not np.allclose(matrix_op.sum(axis=1), 1.0, atol=1e-5):
                     raise ValidationError("Influence matrix rows must sum to 1.0")
            else:
                # Sparse Mode: Efficient for large matrices
                matrix_op = csr_matrix(network.matrix)
                # Validate Stochasticity (Sparse)
                # axis=1 returns np.matrix, convert to array -> flatten
                row_sums = np.array(matrix_op.sum(axis=1)).flatten()
                if not np.allclose(row_sums, 1.0, atol=1e-5):
                     raise ValidationError("Influence matrix rows must sum to 1.0")

        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            # If OOM happens during conversion, we might fall back or fail gracefully
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
