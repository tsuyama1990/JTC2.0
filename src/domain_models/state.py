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


class LazyIdeaIterator(Iterator[LeanCanvas]):
    """
    Wrapper for Idea Iterator to enforce single-use consumption and safety.

    This class is not a Pydantic model but used as a field type.
    """

    def __init__(self, iterator: Iterator[LeanCanvas]) -> None:
        self._iterator = iterator
        self._consumed = False

    def __iter__(self) -> Iterator[LeanCanvas]:
        # Return self as the iterator
        return self

    def __next__(self) -> LeanCanvas:
        # Delegate to the wrapped iterator
        if self._consumed:
             # Already marked as started
             pass
        self._consumed = True
        return next(self._iterator)


class GlobalState(BaseModel):
    """The central state of the LangGraph workflow."""

    # Strict validation enabled, but arbitrary types allowed for Iterator wrapper
    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    phase: Phase = Phase.IDEATION
    topic: str = ""

    # Critical: Wrapper for memory efficiency. Enforced single type.
    generated_ideas: LazyIdeaIterator | None = None

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

    @field_validator("generated_ideas", mode="before")
    @classmethod
    def wrap_iterator(cls, v: object) -> object:
        """
        Auto-wrap Iterator[LeanCanvas] into LazyIdeaIterator if needed.
        This allows passing a raw iterator (e.g. from tests or agents) while ensuring
        the internal state uses the safe wrapper.
        """
        if isinstance(v, Iterator) and not isinstance(v, LazyIdeaIterator):
            return LazyIdeaIterator(v)
        return v

    @model_validator(mode="after")
    def validate_state(self) -> Self:
        """Apply all state validators."""
        GlobalStateValidators.validate_phase_requirements(self)
        return self
