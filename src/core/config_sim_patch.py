from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings

from src.core.constants import (
    MSG_SIM_TITLE,
)
from src.domain_models.simulation import Role


class SimulationStep(BaseSettings):
    """Configuration for a single step in the simulation."""
    node_name: str
    role: Role
    description: str


class SimulationConfig(BaseSettings):
    """Configuration for the Pyxel Simulation UI and Logic."""

    # ... (existing UI config fields)
    width: int = Field(default=800, description="Window width")
    height: int = Field(default=600, description="Window height")
    fps: int = Field(default=30, description="Frames per second")
    title: str = Field(default=MSG_SIM_TITLE, description="Window title")
    # ... other existing fields ...

    # Turn Sequence Configuration
    turn_sequence: list[dict[str, Any]] = Field(
        default_factory=lambda: [
            {"node_name": "pitch", "role": Role.NEW_EMPLOYEE, "description": "New Employee Pitch"},
            {"node_name": "finance_critique", "role": Role.FINANCE, "description": "Finance Critique"},
            {"node_name": "defense_1", "role": Role.NEW_EMPLOYEE, "description": "New Employee Defense"},
            {"node_name": "sales_critique", "role": Role.SALES, "description": "Sales Critique"},
            {"node_name": "defense_2", "role": Role.NEW_EMPLOYEE, "description": "New Employee Final Defense"},
        ],
        description="List of simulation steps defining the turn sequence."
    )

    # ... (rest of the config)
