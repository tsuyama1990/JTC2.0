import logging

from src.core.config import NemawashiConfig, get_settings
from src.core.nemawashi.analytics import AnalyticsService
from src.core.nemawashi.consensus import ConsensusService
from src.core.nemawashi.nomikai import SimulationService
from src.domain_models.politics import InfluenceNetwork

logger = logging.getLogger(__name__)


class NemawashiEngine:
    """
    Core engine for Nemawashi (Consensus Building).
    Acts as a facade over Consensus, Analytics, and Simulation services to maintain SRP
    while providing a unified interface for graph nodes.
    """

    def __init__(self, settings: NemawashiConfig | None = None) -> None:
        self.settings = settings or get_settings().nemawashi
        self.consensus_service = ConsensusService(self.settings)
        self.analytics_service = AnalyticsService()
        self.simulation_service = SimulationService(self.settings)

    def calculate_consensus(self, network: InfluenceNetwork) -> list[float]:
        """
        Delegates consensus calculation to ConsensusService.
        """
        return self.consensus_service.calculate_consensus(network)

    def identify_influencers(self, network: InfluenceNetwork) -> list[str]:
        """
        Delegates influencer identification to AnalyticsService.
        """
        return self.analytics_service.identify_influencers(network)

    def run_nomikai(self, network: InfluenceNetwork, target_name: str) -> InfluenceNetwork:
        """
        Delegates the Nomikai simulation to SimulationService.
        """
        return self.simulation_service.run_nomikai(network, target_name)
