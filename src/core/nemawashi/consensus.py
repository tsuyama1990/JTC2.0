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

    def _validate_stochasticity(self, row_sums: np.ndarray) -> None:
        """Ensure all rows sum to 1.0."""
        if not np.allclose(row_sums, 1.0, atol=1e-5):
             msg = "Influence matrix rows must sum to 1.0"
             raise ValidationError(msg)

    def calculate_consensus(self, network: InfluenceNetwork) -> list[float]:
        """
        Run the DeGroot model to calculate final opinion distribution.

        Strategy:
        - ALWAYS use Sparse Matrices (csr_matrix) to avoid OOM on large datasets and double memory usage.
        - Audit Requirement: "NEVER load entire datasets into memory."
        - Although input is a list of lists, converting to dense numpy array would duplicate memory usage.
          Converting directly to CSR is more efficient for the multiplication steps.
        """
        opinions = np.array([s.initial_support for s in network.stakeholders])

        try:
            # Sparse Mode: Default for everything to prevent OOM and double memory allocation
            # efficient for matrix-vector multiplication in the loop
            matrix_op = csr_matrix(network.matrix)

            # Validate Stochasticity (Sparse)
            # axis=1 returns np.matrix, convert to array -> flatten
            row_sums = np.array(matrix_op.sum(axis=1)).flatten()
            self._validate_stochasticity(row_sums)

        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            # If OOM happens during conversion, we might fall back or fail gracefully
            msg = f"Failed to process matrix: {e}"
            raise ValidationError(msg) from e

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
