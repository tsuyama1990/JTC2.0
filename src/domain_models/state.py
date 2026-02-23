from collections.abc import Iterator
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, model_validator

from src.core.config import get_settings

from .lean_canvas import LeanCanvas
from .metrics import Metrics
from .mvp import MVP
from .persona import Persona
from .simulation import DialogueMessage


class Phase(StrEnum):
    IDEATION = "ideation"
    VERIFICATION = "verification"
    SOLUTION = "solution"
    PMF = "pmf"


class GlobalStateValidators:
    """Encapsulates validation logic for GlobalState."""

    @staticmethod
    def validate_phase_requirements(state: "GlobalState") -> "GlobalState":
        """Validate that required fields are present for the current phase."""
        settings = get_settings()
        if state.phase == Phase.VERIFICATION and state.target_persona is None:
            raise ValueError(settings.errors.missing_persona)
        if state.phase == Phase.SOLUTION and state.mvp_definition is None:
            raise ValueError(settings.errors.missing_mvp)
        return state


class GlobalState(BaseModel):
    """The central state of the LangGraph workflow."""

    # Strict validation enabled
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    phase: Phase = Phase.IDEATION
    topic: str = ""
    # Changed from Iterable to Iterator to enforce streaming contract
    generated_ideas: Iterator[LeanCanvas] | None = None
    selected_idea: LeanCanvas | None = None
    messages: list[str] = []

    target_persona: Persona | None = None
    mvp_definition: MVP | None = None
    metrics_data: Metrics | None = None

    debate_history: list[DialogueMessage] = []
    simulation_active: bool = False

    @model_validator(mode="after")
    def validate_state(self) -> Self:
        """Apply all state validators."""
        GlobalStateValidators.validate_phase_requirements(self)
        return self
