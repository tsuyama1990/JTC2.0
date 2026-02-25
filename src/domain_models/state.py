from collections.abc import Iterator
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.core.config import get_settings
from src.domain_models.common import LazyIdeaIterator
from src.domain_models.enums import Phase, Role
from src.domain_models.validators import StateValidator

__all__ = ["GlobalState", "Phase"]

from .lean_canvas import LeanCanvas
from .metrics import Metrics, RingiSho
from .mvp import MVP, MVPSpec
from .persona import Persona
from .politics import InfluenceNetwork
from .simulation import AgentState, DialogueMessage
from .transcript import Transcript


class GlobalState(BaseModel):
    """The central state of the LangGraph workflow."""

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

    # Cycle 5: MVP Generation (v0.dev)
    mvp_spec: MVPSpec | None = None
    mvp_url: str | None = None
    candidate_features: list[str] = Field(
        default_factory=list, description="List of extracted features for selection"
    )
    selected_feature: str | None = None

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
    influence_network: InfluenceNetwork | None = None
    ringi_sho: RingiSho | None = None

    @field_validator("transcripts")
    @classmethod
    def validate_unique_transcripts(cls, v: list[Transcript]) -> list[Transcript]:
        """Ensure transcripts are unique by source."""
        # Simple list validation logic, keeping it here for field proximity or move to validator?
        # The audit asked to "Extract complex validation logic".
        # This is relatively simple, but let's be strict.
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
        StateValidator.validate_phase_requirements(self)
        return self
