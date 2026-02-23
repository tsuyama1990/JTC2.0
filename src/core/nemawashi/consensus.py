import logging
import typing

import numpy as np

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
        Uses chunked processing to avoid loading the entire matrix into numpy at once if possible.
        """
        opinions = np.array([s.initial_support for s in network.stakeholders])

        # Determine if we should chunk based on size
        chunk_size = 1000

        # Validate stochasticity (Chunked to be safe)
        self._validate_stochasticity_list(network.matrix, chunk_size)

        max_steps = self.settings.max_steps
        tolerance = self.settings.tolerance

        current_ops = opinions

        for _ in range(max_steps):
            # Always use chunked logic for consistent memory usage
            next_ops = self._chunked_dot_list(network.matrix, current_ops, chunk_size)

            if np.allclose(current_ops, next_ops, atol=tolerance):
                logger.info("Consensus converged.")
                return typing.cast(list[float], next_ops.tolist())
            current_ops = next_ops

        return typing.cast(list[float], current_ops.tolist())

    def _validate_stochasticity_list(self, matrix: list[list[float]], chunk_size: int = 1000) -> None:
        """Ensure rows sum to 1.0 using chunked processing."""
        rows = len(matrix)
        for i in range(0, rows, chunk_size):
            end = min(i + chunk_size, rows)
            chunk = np.array(matrix[i:end])
            row_sums = chunk.sum(axis=1)
            if not np.allclose(row_sums, 1.0, atol=1e-5):
                msg = "Influence matrix rows must sum to 1.0"
                raise ValidationError(msg)

    def _chunked_dot_list(
        self, matrix: list[list[float]], vector: np.ndarray, chunk_size: int = 1000
    ) -> np.ndarray:
        """
        Perform matrix-vector multiplication in chunks taking List[List] as input.
        Converts chunks to numpy on the fly to avoid full dense allocation.
        """
        rows = len(matrix)
        result = np.zeros(rows)

        for i in range(0, rows, chunk_size):
            end = min(i + chunk_size, rows)
            # Slicing a list creates a copy of references, lightweight
            chunk_list = matrix[i:end]
            chunk_np = np.array(chunk_list)
            result[i:end] = chunk_np.dot(vector)

        return result
