from collections import deque
from collections.abc import Iterator
from typing import Any, Self

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
    messages: deque[str] = Field(
        default_factory=lambda: deque(maxlen=get_settings().simulation.max_messages)
    )

    target_persona: Persona | None = None

    mvp_definition: MVP | None = None
    metrics_data: Metrics | None = None

    # Cycle 5: MVP Generation (v0.dev)
    mvp_spec: MVPSpec | None = None
    mvp_url: str | None = None
    candidate_features: deque[str] = Field(
        default_factory=lambda: deque(maxlen=100),
        description="List of extracted features for selection",
    )
    selected_feature: str | None = None

    debate_history: deque[DialogueMessage] = Field(default_factory=lambda: deque(maxlen=1000))
    simulation_active: bool = False

    # Updated fields for Cycle 3
    transcripts: deque[Transcript] = Field(
        default_factory=lambda: deque(maxlen=100),
        description="Raw transcripts from PLAUD or interviews",
    )
    rag_index_path: str = Field(
        default="",
        description="Path to the local vector store",
    )

    @model_validator(mode="before")
    @classmethod
    def set_rag_index_path(cls, data: Any) -> Any:
        from pathlib import Path

        if isinstance(data, dict):
            path = data.get("rag_index_path") or get_settings().rag_persist_dir
            Path(path).mkdir(parents=True, exist_ok=True)
            data["rag_index_path"] = path
        return data

    agent_states: dict[Role, AgentState] = Field(
        default_factory=dict, description="Persistent state of agents (e.g. DeGroot weights)"
    )
    influence_network: InfluenceNetwork | None = None
    ringi_sho: RingiSho | None = None

    @field_validator("transcripts")
    @classmethod
    def validate_unique_transcripts(cls, v: deque[Transcript]) -> deque[Transcript]:
        """Ensure transcripts are unique by source in O(n) complexity."""
        seen_sources: set[str] = set()
        for t in v:
            if t.source in seen_sources:
                msg = f"Duplicate transcript source found: {t.source}"
                raise ValueError(msg)
            seen_sources.add(t.source)
        return v

    @field_validator("agent_states")
    @classmethod
    def validate_agent_states(cls, v: dict[Role, AgentState]) -> dict[Role, AgentState]:
        """Ensure agent_states keys match the AgentState role."""
        limit = get_settings().simulation.max_agents
        if len(v) > limit:
            msg = f"Too many agent states ({len(v)}). Exceeds memory safety limits ({limit})."
            raise ValueError(msg)
        for role, state in v.items():
            if role != state.role:
                msg = f"Key {role} does not match AgentState role {state.role}"
                raise ValueError(msg)
        return v

    @field_validator("generated_ideas", mode="before")
    @classmethod
    def wrap_iterator(cls, v: Any) -> Any:
        """
        Auto-wrap Iterator[LeanCanvas] into LazyIdeaIterator if needed.
        Strictly enforces that the input is a valid Iterator.
        """
        if v is None:
            return None

        if isinstance(v, LazyIdeaIterator):
            return v

        if isinstance(v, Iterator) or hasattr(v, "__iter__"):
            return LazyIdeaIterator(v)

        # Reject invalid types explicitly
        msg = f"generated_ideas must be an Iterator or LazyIdeaIterator, got {type(v)}"
        raise TypeError(msg)

    @model_validator(mode="after")
    def auto_validate_state(self) -> Self:
        """Lightweight automatic validation hooks on state change."""
        limit = get_settings().simulation.max_messages
        if len(self.messages) > limit:
            msg = f"Messages list ({len(self.messages)}) exceeded safety limit ({limit})."
            raise ValueError(msg)
        return self

    def validate_state(self) -> Self:
        """Apply full business phase state validation manually (to avoid heavy loop lags)."""
        StateValidator.validate_phase_requirements(self)
        return self
