import logging
import typing

import numpy as np
from scipy.sparse import csgraph

from src.core.config import get_settings
from src.core.constants import ERR_DISCONNECTED_GRAPH
from src.core.exceptions import CalculationError, NetworkError, ValidationError
from src.domain_models.politics import InfluenceNetwork

logger = logging.getLogger(__name__)


class NemawashiEngine:
    """Core logic for French-DeGroot consensus building."""

    def __init__(self) -> None:
        self.settings = get_settings().nemawashi

    def calculate_consensus(self, network: InfluenceNetwork) -> list[float]:
        """
        Run the DeGroot model to calculate final opinion distribution.
        """
        # Convert to numpy
        matrix = np.array(network.matrix)
        opinions = np.array([s.initial_support for s in network.stakeholders])

        # Validate Stochasticity
        self._validate_stochasticity(matrix)

        # Check connectivity
        if not self._is_connected(matrix):
            logger.warning(ERR_DISCONNECTED_GRAPH)
            raise NetworkError(ERR_DISCONNECTED_GRAPH)

        max_steps = self.settings.max_steps
        tolerance = self.settings.tolerance

        # Run iteration using French-DeGroot update rule
        current_ops = opinions
        rows = matrix.shape[0]

        # Determine if we should chunk
        chunk_size = 1000 # Could be configurable, but 1000 is reasonable default
        use_chunking = rows > chunk_size

        for _ in range(max_steps):
            if use_chunking:
                next_ops = self._chunked_dot(matrix, current_ops, chunk_size)
            else:
                next_ops = matrix.dot(current_ops)

            if np.allclose(current_ops, next_ops, atol=tolerance):
                logger.info("Consensus converged.")
                return typing.cast(list[float], next_ops.tolist())
            current_ops = next_ops

        return typing.cast(list[float], current_ops.tolist())

    def identify_influencers(self, network: InfluenceNetwork) -> list[str]:
        """
        Identify key influencers based on centrality/eigenvectors.
        """
        matrix = np.array(network.matrix)

        # Basic validation before expensive operation
        if matrix.shape[0] == 0:
            return []

        # Check for NaN or Inf
        if not np.all(np.isfinite(matrix)):
             msg = "Influence matrix contains NaN or Inf values."
             raise ValidationError(msg)

        try:
            # Use eig on transpose to find left eigenvectors (vW = v)
            eigenvalues, eigenvectors = np.linalg.eig(matrix.T)

            # Find index of eigenvalue 1 (real part close to 1)
            # Row stochastic matrices always have eigenvalue 1.
            idx = np.argmin(np.abs(eigenvalues - 1.0))

            centrality = np.abs(eigenvectors[:, idx])
            # Normalize
            if np.sum(centrality) > 0:
                centrality = centrality / np.sum(centrality)

            # Rank stakeholders
            indices = np.argsort(centrality)[::-1]  # Descending
            return [network.stakeholders[i].name for i in indices]

        except np.linalg.LinAlgError as e:
            msg = "Eigenvector calculation failed"
            logger.exception(msg)
            error_msg = f"{msg}: {e}"
            raise CalculationError(error_msg) from e

    def run_nomikai(self, network: InfluenceNetwork, target_name: str) -> InfluenceNetwork:
        """
        Simulate a 'Nomikai' event to boost support and reduce stubbornness.
        Returns a NEW InfluenceNetwork (immutable).
        """
        # Immutable update
        new_network = network.model_copy(deep=True)

        target_idx = -1
        for i, s in enumerate(new_network.stakeholders):
            if s.name == target_name:
                target_idx = i
                break

        if target_idx == -1:
            msg = f"Target {target_name} not found."
            raise ValidationError(msg)

        # 1. Boost Support
        self._boost_support(new_network, target_idx)

        # 2. Reduce Stubbornness (Self-weight)
        self._redistribute_stubbornness(new_network, target_idx)

        return new_network

    def _boost_support(self, network: InfluenceNetwork, idx: int) -> None:
        """Increase the initial support of the stakeholder."""
        current_supp = network.stakeholders[idx].initial_support
        boost = self.settings.nomikai_boost
        new_supp = min(1.0, current_supp + (1.0 - current_supp) * boost)
        network.stakeholders[idx].initial_support = new_supp

    def _redistribute_stubbornness(self, network: InfluenceNetwork, idx: int) -> None:
        """Reduce self-weight and redistribute to others."""
        reduction = self.settings.nomikai_reduction
        matrix = network.matrix
        row = matrix[idx]
        old_self = row[idx]

        new_self = max(0.0, old_self - reduction)
        diff = old_self - new_self

        # Distribute diff to others
        n = len(row)
        if n > 1:
            others_count = n - 1
            add_per_person = diff / others_count
            for j in range(n):
                if j == idx:
                    row[j] = new_self
                else:
                    row[j] += add_per_person

        # Update stakeholder stubborness field too for consistency
        network.stakeholders[idx].stubbornness = new_self

    def _validate_stochasticity(self, matrix: np.ndarray) -> None:
        """Ensure rows sum to 1.0."""
        row_sums = matrix.sum(axis=1)
        if not np.allclose(row_sums, 1.0, atol=1e-5):
            msg = "Influence matrix rows must sum to 1.0"
            raise ValidationError(msg)

    def _chunked_dot(
        self, matrix: np.ndarray, vector: np.ndarray, chunk_size: int = 1000
    ) -> np.ndarray:
        """
        Perform matrix-vector multiplication in chunks to avoid large memory allocation.
        Result = M . v
        """
        rows = matrix.shape[0]
        result = np.zeros(rows)

        for i in range(0, rows, chunk_size):
            end = min(i + chunk_size, rows)
            chunk = matrix[i:end]
            result[i:end] = chunk.dot(vector)

        return result

    def _is_connected(self, matrix: np.ndarray) -> bool:
        """Check if graph has a single component (weakly connected)."""
        # Convert to boolean adjacency
        adj = matrix > 0
        n_components, _ = csgraph.connected_components(adj, connection="weak")
        return int(n_components) == 1
