from collections.abc import Iterator
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.core.config import get_settings

from .lean_canvas import LeanCanvas
from .metrics import Metrics
from .mvp import MVP
from .persona import Persona
from .simulation import AgentState, DialogueMessage, Role


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


class LazyIdeaIterator:
    """
    Wrapper for Idea Iterator to enforce single-use consumption and safety.

    This class is not a Pydantic model but used as a field type.
    """

    def __init__(self, iterator: Iterator[LeanCanvas]) -> None:
        self._iterator = iterator
        self._consumed = False

    def __iter__(self) -> Iterator[LeanCanvas]:
        if self._consumed:
            msg = "Iterator already consumed. Cannot re-iterate."
            raise RuntimeError(msg)
        self._consumed = True
        return self._iterator

    def next(self) -> LeanCanvas:
        return next(self._iterator)


class GlobalState(BaseModel):
    """The central state of the LangGraph workflow."""

    # Strict validation enabled, but arbitrary types allowed for Iterator wrapper
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    phase: Phase = Phase.IDEATION
    topic: str = ""

    # Critical: Wrapper for memory efficiency.
    generated_ideas: LazyIdeaIterator | Iterator[LeanCanvas] | None = None

    selected_idea: LeanCanvas | None = None
    messages: list[str] = Field(default_factory=list)

    target_persona: Persona | None = None
    mvp_definition: MVP | None = None
    metrics_data: Metrics | None = None

    debate_history: list[DialogueMessage] = Field(default_factory=list)
    simulation_active: bool = False

    # New fields for architecture compliance
    transcript: str | None = Field(default=None, description="Raw transcript from PLAUD or interviews")
    agent_states: dict[Role, AgentState] = Field(
        default_factory=dict,
        description="Persistent state of agents (e.g. DeGroot weights)"
    )

    @field_validator("transcript")
    @classmethod
    def validate_transcript(cls, v: str | None) -> str | None:
        """Ensure transcript, if provided, is not trivial."""
        if v is not None and len(v.strip()) < 10:
            msg = "Transcript is too short to be valid."
            raise ValueError(msg)
        return v

    @field_validator("agent_states")
    @classmethod
    def validate_agent_states(cls, v: dict[Role, AgentState]) -> dict[Role, AgentState]:
        """Ensure agent_states keys match the AgentState role."""
        for role, state in v.items():
            if role != state.role:
                msg = f"Key {role} does not match AgentState role {state.role}"
                raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_state(self) -> Self:
        """Apply all state validators."""
        GlobalStateValidators.validate_phase_requirements(self)
        return self
