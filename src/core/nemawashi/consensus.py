import logging

from src.core.config import NemawashiConfig, get_settings
from src.core.nemawashi.utils import NemawashiUtils
from src.domain_models.politics import InfluenceNetwork

logger = logging.getLogger(__name__)


class ConsensusService:
    """
    Handles the core mathematical consensus building (French-DeGroot Model).
    """

    def __init__(self, settings: NemawashiConfig | None = None) -> None:
        """
        Initialize the Consensus Service.

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

        from src.core.exceptions import ValidationError

        # Use settings for max_steps, no hardcoded default in logic
        max_steps = self.settings.max_steps
        tolerance = self.settings.tolerance

        matrix_op = None
        max_retries = 3

        # Retry loop for validation failures
        for attempt in range(max_retries):
            try:
                # Build Sparse Matrix using shared utility
                matrix_op = NemawashiUtils.build_sparse_matrix(network, n)

                # Validate using shared utility
                NemawashiUtils.validate_stochasticity(matrix_op, tolerance)

                # If validation passes, break out of retry loop
                break
            except ValidationError as e:
                logger.warning(f"Stochasticity validation failed on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    logger.exception("Max retries reached for stochasticity validation.")
                    raise

                # Fallback mechanism: auto-normalize the matrix to enforce stochasticity
                logger.info("Applying auto-normalization fallback.")
                if matrix_op is not None:
                    try:
                        import numpy as np

                        row_sums = np.array(matrix_op.sum(axis=1)).flatten()
                        # Prevent division by zero
                        row_sums[row_sums == 0] = 1.0

                        from scipy.sparse import diags

                        inv_diag = diags(1.0 / row_sums)
                        matrix_op = inv_diag.dot(matrix_op)
                        # Fallback succeeded, use this matrix and break out of the retry loop
                        break
                    except Exception as norm_e:
                        logger.warning(f"Normalization fallback failed: {norm_e}")

        if matrix_op is None:
            return []

        current_ops = opinions

        for _ in range(max_steps):
            # Sparse Matrix-Vector Multiplication
            next_ops = matrix_op.dot(current_ops)

            if np.allclose(current_ops, next_ops, atol=tolerance):
                logger.info("Consensus converged.")
                return list(next_ops)
            current_ops = next_ops

        return list(current_ops)
