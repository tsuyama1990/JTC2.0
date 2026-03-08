from collections import deque
from collections.abc import Iterator
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.core.config import get_settings
from src.domain_models.common import create_lazy_iterator
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


class SimulationState(BaseModel):
    """State concerning the Pyxel UI and agent debate simulation."""

    model_config = ConfigDict(extra="forbid")

    debate_history: deque[DialogueMessage] = Field(default_factory=lambda: deque(maxlen=1000))
    simulation_active: bool = False
    agent_states: dict[Role, AgentState] = Field(
        default_factory=dict, description="Persistent state of agents (e.g. DeGroot weights)"
    )
    influence_network: InfluenceNetwork | None = None

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


class RAGState(BaseModel):
    """State concerning retrieval-augmented generation."""

    model_config = ConfigDict(extra="forbid")

    transcripts: deque[Transcript] = Field(
        default_factory=lambda: deque(maxlen=100),
        description="Raw transcripts from PLAUD or interviews",
    )
    rag_index_path: str = Field(
        default_factory=lambda: get_settings().rag_persist_dir,
        description="Path to the local vector store",
    )

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


class GlobalState(BaseModel):
    """The central state of the LangGraph workflow."""

    model_config = ConfigDict(extra="forbid")

    phase: Phase = Phase.IDEATION
    topic: str = ""

    # Critical: Wrapper for memory efficiency.
    # We use a validator to ensure it's the right type.
    generated_ideas: Any = None

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

    ringi_sho: RingiSho | None = None

    # Composed states
    sim_state: SimulationState = Field(default_factory=SimulationState)
    rag_state: RAGState = Field(default_factory=RAGState)

    # Delegation properties to maintain backward compatibility for existing logic
    @property
    def debate_history(self) -> deque[DialogueMessage]:
        return self.sim_state.debate_history

    @debate_history.setter
    def debate_history(self, value: deque[DialogueMessage]) -> None:
        self.sim_state.debate_history = value

    @property
    def simulation_active(self) -> bool:
        return self.sim_state.simulation_active

    @simulation_active.setter
    def simulation_active(self, value: bool) -> None:
        self.sim_state.simulation_active = value

    @property
    def agent_states(self) -> dict[Role, AgentState]:
        return self.sim_state.agent_states

    @agent_states.setter
    def agent_states(self, value: dict[Role, AgentState]) -> None:
        self.sim_state.agent_states = value

    @property
    def influence_network(self) -> InfluenceNetwork | None:
        return self.sim_state.influence_network

    @influence_network.setter
    def influence_network(self, value: InfluenceNetwork | None) -> None:
        self.sim_state.influence_network = value

    @property
    def transcripts(self) -> deque[Transcript]:
        return self.rag_state.transcripts

    @transcripts.setter
    def transcripts(self, value: deque[Transcript]) -> None:
        self.rag_state.transcripts = value

    @property
    def rag_index_path(self) -> str:
        return self.rag_state.rag_index_path

    @rag_index_path.setter
    def rag_index_path(self, value: str) -> None:
        self.rag_state.rag_index_path = value

    @field_validator("generated_ideas", mode="before")
    @classmethod
    def wrap_iterator(cls, v: Any) -> Any:
        """
        Auto-wrap Iterator[LeanCanvas] into size-limited generator if needed.
        """
        if v is None:
            return None

        from collections.abc import Generator

        if isinstance(v, Generator):
            return v

        if isinstance(v, Iterator) or hasattr(v, "__iter__"):
            return create_lazy_iterator(v)

        msg = f"generated_ideas must be an Iterator, got {type(v)}"
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
