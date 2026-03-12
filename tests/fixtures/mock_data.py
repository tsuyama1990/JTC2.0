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
