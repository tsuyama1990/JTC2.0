import logging

from src.core.config import NemawashiConfig, get_settings
from src.core.nemawashi.utils import NemawashiUtils
from src.domain_models.politics import InfluenceNetwork

logger = logging.getLogger(__name__)


class ConsensusEngine:
    """
    Handles the core mathematical consensus building (French-DeGroot Model).
    """

    def __init__(self, settings: NemawashiConfig | None = None) -> None:
        """
        Initialize the Consensus Engine.

        Args:
            settings: Configuration settings for Nemawashi. If None, loads from global settings.
        """
        self.settings = settings or get_settings().nemawashi

    def calculate_consensus(self, network: InfluenceNetwork) -> list[float]:
        """
        Run the DeGroot model to calculate final opinion distribution.
        Always uses sparse matrices (CSR) for memory efficiency.

        Args:
            network: The influence network containing stakeholders and weights.

        Returns:
            A list of final opinion values (0.0 to 1.0) for each stakeholder.
        """
        n = len(network.stakeholders)
        if n == 0:
            return []

        # Convert opinions to numpy array
        import numpy as np
        opinions = np.array([s.initial_support for s in network.stakeholders], dtype=float)

        # Build Sparse Matrix using shared utility
        matrix_op = NemawashiUtils.build_sparse_matrix(network, n)

        # Validate using shared utility
        NemawashiUtils.validate_stochasticity(matrix_op, self.settings.tolerance)

        # Use settings for max_steps, no hardcoded default in logic
        max_steps = self.settings.max_steps
        tolerance = self.settings.tolerance

        current_ops = opinions

        for _ in range(max_steps):
            # Sparse Matrix-Vector Multiplication
            next_ops = matrix_op.dot(current_ops)

            if np.allclose(current_ops, next_ops, atol=tolerance):
                logger.info("Consensus converged.")
                return list(next_ops) # type: ignore
            current_ops = next_ops

        return list(current_ops) # type: ignore
