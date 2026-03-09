from src.core.config import NemawashiConfig, get_settings
from src.core.nemawashi.analytics import InfluenceAnalyzer
from src.core.nemawashi.consensus import ConsensusEngine
from src.core.nemawashi.nomikai import NomikaiSimulator
from src.domain_models.politics import InfluenceNetwork


class NemawashiEngine:
    """
    Core engine for Nemawashi (Consensus Building).
    Aggregates consensus calculation, analytics, and simulation logic through dependency injection.
    """

    def __init__(
        self,
        consensus: ConsensusEngine | None = None,
        analytics: InfluenceAnalyzer | None = None,
        simulator: NomikaiSimulator | None = None,
        settings: NemawashiConfig | None = None,
    ) -> None:
        self.settings = settings or get_settings().nemawashi
        self.consensus = consensus or ConsensusEngine(self.settings)
        self.analytics = analytics or InfluenceAnalyzer()
        self.simulator = simulator or NomikaiSimulator(self.settings)

    def calculate_consensus(self, network: InfluenceNetwork) -> list[float]:
        """Run the DeGroot model to calculate final opinion distribution."""
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
