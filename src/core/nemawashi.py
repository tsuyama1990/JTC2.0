import logging

import numpy as np

from src.domain_models.politics import InfluenceNetwork

logger = logging.getLogger(__name__)


class NemawashiEngine:
    """
    Implements the French-DeGroot opinion dynamics model.
    """

    def calculate_consensus(
        self, network: InfluenceNetwork, max_steps: int = 100, tolerance: float = 1e-6
    ) -> dict[str, float]:
        """
        Calculates the consensus opinions after simulating the network.

        Args:
            network: The influence network.
            max_steps: Maximum number of simulation steps.
            tolerance: Convergence tolerance.

        Returns:
            A dictionary mapping stakeholder names to their final support score (0.0 to 1.0).
        """
        if not network.stakeholders:
            return {}

        # Opinion vector x(0)
        x = np.array([s.initial_support for s in network.stakeholders])

        # Influence matrix W
        w_matrix = np.array(network.matrix)

        # Validate W is row-stochastic (rows sum to 1)
        # We normalize it to be safe.
        row_sums = w_matrix.sum(axis=1)
        if np.any(row_sums == 0):
            logger.warning(
                "Influence matrix has zero-sum rows. Agents with zero influence out-degree will keep opinion?"
            )
            # If a row sums to 0, it means the agent listens to nobody.
            # We assume they keep their own opinion (stubbornness = 1.0 effectively).
            # So we set the diagonal element to 1.0 for those rows.
            zero_sum_indices = np.where(row_sums == 0)[0]
            for idx in zero_sum_indices:
                w_matrix[idx, idx] = 1.0

            # Recompute row sums
            row_sums = w_matrix.sum(axis=1)

        w_matrix = w_matrix / row_sums[:, np.newaxis]

        # Simulation loop
        for step in range(max_steps):
            x_new = w_matrix @ x
            if np.allclose(x, x_new, atol=tolerance):
                logger.info(f"Consensus reached at step {step}")
                x = x_new
                break
            x = x_new

        return {s.name: float(val) for s, val in zip(network.stakeholders, x, strict=True)}

    def run_nomikai(
        self, network: InfluenceNetwork, target_name: str, influencer_name: str
    ) -> InfluenceNetwork:
        """
        Simulates a 'Nomikai' (Drinking Party) where social barriers are lowered.
        Increases the weight of the influencer on the target, reducing target's stubbornness.

        Args:
            network: The current network.
            target_name: The name of the stakeholder being targeted.
            influencer_name: The name of the stakeholder influencing (e.g., User/New Employee).

        Returns:
            A NEW InfluenceNetwork with modified weights.
        """
        # Find indices
        try:
            target_idx = next(i for i, s in enumerate(network.stakeholders) if s.name == target_name)
            influencer_idx = next(
                i for i, s in enumerate(network.stakeholders) if s.name == influencer_name
            )
        except StopIteration:
            logger.exception(f"Stakeholder not found: {target_name} or {influencer_name}")
            return network

        new_matrix = [row[:] for row in network.matrix]

        # Boost influencer weight, reduce self weight (stubbornness)
        boost = 0.3

        new_matrix[target_idx][influencer_idx] += boost
        new_matrix[target_idx][target_idx] -= boost

        # Clamp self weight to 0
        if new_matrix[target_idx][target_idx] < 0:
            new_matrix[target_idx][target_idx] = 0.0

        # Normalize the row
        row = np.array(new_matrix[target_idx])
        if row.sum() > 0:
            row = row / row.sum()
        new_matrix[target_idx] = row.tolist()

        # Update stakeholders (sync stubbornness)
        new_stakeholders = [s.model_copy() for s in network.stakeholders]
        new_stakeholders[target_idx].stubbornness = new_matrix[target_idx][target_idx]

        return InfluenceNetwork(stakeholders=new_stakeholders, matrix=new_matrix)

    def identify_influencers(self, network: InfluenceNetwork) -> list[str]:
        """
        Identifies key influencers based on centrality or weight in the matrix.
        For DeGroot, eigenvector centrality on the transpose of W corresponds to social influence.
        The left eigenvector associated with eigenvalue 1.
        """
        if not network.stakeholders:
            return []

        w_matrix = np.array(network.matrix)

        # Normalize W
        row_sums = w_matrix.sum(axis=1)
        row_sums[row_sums == 0] = 1.0
        w_matrix = w_matrix / row_sums[:, np.newaxis]

        # Calculate eigenvector centrality (left eigenvector for eigenvalue 1)
        # vW = v => W.T v = v
        # We use numpy.linalg.eig
        evals, evecs = np.linalg.eig(w_matrix.T)

        # Find the index of eigenvalue closest to 1
        idx = np.argmin(np.abs(evals - 1.0))

        # Get the eigenvector (take real part and abs)
        centrality = np.abs(evecs[:, idx])

        # Rank stakeholders
        ranking = sorted(
            zip([s.name for s in network.stakeholders], centrality, strict=True),
            key=lambda x: x[1],
            reverse=True,
        )

        return [name for name, _score in ranking]
