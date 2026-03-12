from typing import Any


def get_mock_canvas_data() -> dict[str, Any]:
    """
    Provides a deterministic mock data dictionary for a LeanCanvas.
    This avoids importing from src/ to maintain strict separation of concerns
    between test fixtures and production models.
    """
    return {
        "id": 1,
        "title": "AI for Plumbers",
        "problem": "Scheduling is hard",
        "customer_segments": "Independent Plumbers",
        "unique_value_prop": "Automated Scheduling",
        "solution": "AI Assistant",
        "status": "draft",
    }
