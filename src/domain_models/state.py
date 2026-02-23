from collections.abc import Iterator
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.core.config import get_settings
from src.domain_models.common import LazyIdeaIterator

from .lean_canvas import LeanCanvas
from .metrics import Metrics
from .mvp import MVP
from .persona import Persona
from .politics import InfluenceNetwork
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


class GlobalState(BaseModel):
    """The central state of the LangGraph workflow."""

    # Updated: Strict typing only, no arbitrary types allowed by default if possible.
    # However, LazyIdeaIterator IS a custom type.
    # The fix is to ensure LazyIdeaIterator is compatible or explicitly allowed ONLY for that field if needed,
    # or rely on Pydantic's handling of iterators if wrapped correctly.
    # But LazyIdeaIterator is a class. Pydantic needs `arbitrary_types_allowed` for non-pydantic types unless
    # we add `__get_pydantic_core_schema__` to LazyIdeaIterator.
    # A simpler approach is to keep strict=True but allow arbitrary for specific fields if Pydantic supports per-field config,
    # which it doesn't easily in V2 without the global config or the schema method.
    #
    # Given the constraint "Remove arbitrary_types_allowed=True", we must make LazyIdeaIterator Pydantic-compatible.
    # BUT modifying common.py to add pydantic schema might be complex.
    # Alternative: The instruction says "implement proper type validation".
    # We can try removing the config and see if Pydantic accepts the Iterator subclass if we just validate it.
    # If not, we might need to add `ignored_types` or similar, but the instruction is strict.
    #
    # Let's try removing it. If it fails, we add the schema method to LazyIdeaIterator.
    model_config = ConfigDict(extra="forbid")

    phase: Phase = Phase.IDEATION
    topic: str = ""

    # Critical: Wrapper for memory efficiency.
    # We use a validator to ensure it's the right type.
    generated_ideas: LazyIdeaIterator | None = None

    selected_idea: LeanCanvas | None = None
    messages: list[str] = Field(default_factory=list)

    target_persona: Persona | None = None
    mvp_definition: MVP | None = None
    metrics_data: Metrics | None = None

    debate_history: list[DialogueMessage] = Field(default_factory=list)
    simulation_active: bool = False

    # Updated fields for Cycle 3
    transcripts: list[Transcript] = Field(
        default_factory=list, description="Raw transcripts from PLAUD or interviews"
    )
    rag_index_path: str = Field(
        default_factory=lambda: get_settings().rag_persist_dir,
        description="Path to the local vector store",
    )

    agent_states: dict[Role, AgentState] = Field(
        default_factory=dict, description="Persistent state of agents (e.g. DeGroot weights)"
    )

    influence_network: InfluenceNetwork | None = Field(
        default=None, description="The French-DeGroot influence network."
    )

    @field_validator("transcripts")
    @classmethod
    def validate_unique_transcripts(cls, v: list[Transcript]) -> list[Transcript]:
        """Ensure transcripts are unique by source."""
        sources = [t.source for t in v]
        if len(sources) != len(set(sources)):
            msg = "Duplicate transcript sources found."
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
        raise TypeError(msg)

    @model_validator(mode="after")
    def validate_state(self) -> Self:
        """Apply all state validators."""
        GlobalStateValidators.validate_phase_requirements(self)
        return self
