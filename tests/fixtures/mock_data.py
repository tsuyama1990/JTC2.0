import sys
from pathlib import Path

project_root = str(Path(__file__).parent.parent.parent.resolve())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.domain_models.lean_canvas import LeanCanvas


def get_mock_canvas() -> LeanCanvas:
    """Provides a deterministic LeanCanvas fixture for testing and tutorials."""
    return LeanCanvas(
        id=1,
        title="AI for Plumbers",
        problem="Scheduling is hard",
        customer_segments="Independent Plumbers",
        unique_value_prop="Automated Scheduling",
        solution="AI Assistant",
    )
