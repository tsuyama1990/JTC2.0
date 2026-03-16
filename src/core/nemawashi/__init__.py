"""
Internal Nemawashi (Consensus Building) Package.

All domain models are exposed through `src.domain_models.politics`.
Internal services should be instantiated individually:
- `from src.core.nemawashi.analytics import AnalyticsService`
- `from src.core.nemawashi.consensus import ConsensusService`
- `from src.core.nemawashi.nomikai import SimulationService`
"""
