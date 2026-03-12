from src.core.config import NemawashiConfig, get_settings
from src.core.nemawashi.analytics import InfluenceAnalyzer
from src.core.nemawashi.consensus import ConsensusEngine
from src.core.nemawashi.nomikai import NomikaiSimulator
from src.domain_models.politics import InfluenceNetwork


class NemawashiEngine:
    """
    Core engine for Nemawashi (Consensus Building).
    Aggregates consensus calculation, analytics, and simulation logic.
    """

    def __init__(self, settings: NemawashiConfig | None = None) -> None:
        self.settings = settings or get_settings().nemawashi
        self.consensus = ConsensusEngine(self.settings)
        self.analytics = InfluenceAnalyzer()
        self.simulator = NomikaiSimulator(self.settings)

    def calculate_consensus(self, network: InfluenceNetwork) -> list[float]:
        """Run the DeGroot model to calculate final opinion distribution."""
        # Validate network connectivity before consensus calculation
        from src.domain_models.politics import SparseMatrixEntry
        matrix_input: list[list[float]] = network.matrix if not network.matrix or not isinstance(network.matrix[0], SparseMatrixEntry) else self.analytics._sparse_to_dense(network.matrix, len(network.stakeholders)) # type: ignore

        if not self.analytics.is_connected(matrix_input):
            # Fallback behavior: if network is disconnected, consensus is impossible.
            # Return current support levels or handle appropriately.
            import logging
            logging.getLogger(__name__).warning("Influence network is not fully connected. Consensus may not converge globally.")

        return self.consensus.calculate_consensus(network)

    def identify_influencers(self, network: InfluenceNetwork) -> list[str]:
        """Identify key influencers based on centrality."""
        return self.analytics.identify_influencers(network)

    def run_nomikai(self, network: InfluenceNetwork, target_name: str) -> InfluenceNetwork:
        """Simulate a 'Nomikai' event to boost support."""
        return self.simulator.run_nomikai(network, target_name)

    def _is_connected(self, matrix: list[list[float]]) -> bool:
        """Check if graph has a single component (weakly connected)."""
        return self.analytics.is_connected(matrix)
