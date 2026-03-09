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
        self._cache: dict[str, list[float]] = {}

    def calculate_consensus(self, network: InfluenceNetwork) -> list[float]:
        try:
            cache_key = network.model_dump_json()
            if cache_key in self._cache:
                return self._cache[cache_key]

            result = self._calculate_consensus_impl(network)

            if len(self._cache) > 10:
                self._cache.pop(next(iter(self._cache)))

            self._cache[cache_key] = result
        except Exception:
            return self._calculate_consensus_impl(network)
        else:
            return result

    def _calculate_consensus_impl(self, network: InfluenceNetwork) -> list[float]:
        """
        Run the DeGroot model to calculate final opinion distribution.
        Always uses sparse matrices (CSR) for memory efficiency.

        Args:
            network: The influence network containing stakeholders and weights.

        Returns:
            A list of final opinion values (0.0 to 1.0) for each stakeholder.
        """
        if not network or not hasattr(network, "stakeholders") or network.stakeholders is None:
            msg = "Network must contain a valid stakeholders list."
            from src.core.exceptions import ValidationError

            raise ValidationError(msg)

        n = len(network.stakeholders)
        if n == 0:
            return []

        # Convert opinions to numpy array
        import numpy as np

        opinions = np.array([s.initial_support for s in network.stakeholders], dtype=float)

        # Build Sparse Matrix using shared utility
        matrix_op = NemawashiUtils.build_sparse_matrix(network, n)

        # Memory bounds checking: Ensure matrix data footprint is under 100MB
        if matrix_op.data.nbytes > 100 * 1024 * 1024:
            msg = "Network influence matrix exceeds safe memory boundaries."
            raise MemoryError(msg)

        # Validate using shared utility
        NemawashiUtils.validate_stochasticity(matrix_op, self.settings.tolerance)

        # Use settings for max_steps, no hardcoded default in logic
        max_steps = self.settings.max_steps
        tolerance = self.settings.tolerance

        current_ops = opinions

        import time

        start_time = time.time()
        timeout = getattr(self.settings, "timeout", 10.0)

        history = []

        for step in range(max_steps):
            if time.time() - start_time > timeout:
                logger.warning("Consensus calculation timed out.")
                break

            # Sparse Matrix-Vector Multiplication
            next_ops = matrix_op.dot(current_ops)

            if np.allclose(current_ops, next_ops, rtol=tolerance, atol=tolerance):
                logger.info(f"Consensus converged in {step + 1} steps.")
                return list(next_ops)

            # Oscillation detection
            history.append(next_ops)
            if len(history) > 5:
                history.pop(0)
                # Check if the current state is very close to a state 2 steps ago (oscillation)
                if len(history) >= 3 and np.allclose(
                    next_ops, history[-3], rtol=tolerance, atol=tolerance
                ):
                    logger.warning(f"Consensus oscillating. Early termination at step {step + 1}.")
                    # Return the average of the oscillating states
                    return list((next_ops + history[-2]) / 2.0)

            current_ops = next_ops

        logger.warning(f"Consensus stopped. Converged=False. Steps: {max_steps}")
        return list(current_ops)
