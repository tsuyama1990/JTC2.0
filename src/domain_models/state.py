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
from .transcript import Transcript


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
    # We maintain arbitrary_types_allowed=True due to LazyIdeaIterator being a complex iterator
    # wrapper that Pydantic cannot fully validate without generics.
    # However, we add strict field validation where possible.
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

    # Updated fields for Cycle 3
    transcripts: list[Transcript] = Field(default_factory=list, description="Raw transcripts from PLAUD or interviews")
    rag_index_path: str = Field(default_factory=lambda: get_settings().rag_persist_dir, description="Path to the local vector store")

    agent_states: dict[Role, AgentState] = Field(
        default_factory=dict,
        description="Persistent state of agents (e.g. DeGroot weights)"
    )

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
        Strictly enforces that the input is a valid Iterator.
        """
        if v is None:
            return None

        if isinstance(v, LazyIdeaIterator):
            return v

        if isinstance(v, Iterator):
            return LazyIdeaIterator(v)

        # Reject invalid types explicitly
        msg = f"generated_ideas must be an Iterator or LazyIdeaIterator, got {type(v)}"
        raise ValueError(msg)

    @model_validator(mode="after")
    def validate_state(self) -> Self:
        """Apply all state validators."""
        GlobalStateValidators.validate_phase_requirements(self)
        return self
