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
from .politics import InfluenceNetwork, Stakeholder
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

    # Track pivots for looping logic
    # Audit: Add ge=0 and upper bound validation
    pivot_count: int = Field(
        default=0,
        ge=0,
        le=5, # Hardcoded reasonable limit, or load from config if strictly needed. 5 is reasonable for "JTC".
        description="Number of times the user has pivoted."
    )

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

    def _calculate_row(self, i: int, roles: list[Role], agent: AgentState) -> list[float]:
        """Helper to calculate a single row of the influence matrix."""
        row = [0.0] * len(roles)
        profile = agent.degroot_profile

        # Set self-confidence
        row[i] = profile.self_confidence
        current_sum = row[i]

        # Calculate explicit weights
        for other_role_str, weight in profile.influence_weights.items():
            try:
                # Find index of other role
                matches = [idx for idx, r in enumerate(roles) if other_role_str in (r, r.value)]
                if matches:
                    idx = matches[0]
                    if idx != i:
                        row[idx] = weight
                        current_sum += weight
            except (ValueError, IndexError):
                pass

        # Normalize or Distribute Remainder
        remaining = 1.0 - current_sum
        if remaining > 0.0001:
            others_count = len(roles) - 1
            if others_count > 0:
                dist_val = remaining / others_count
                for j in range(len(roles)):
                    if i != j and row[j] == 0.0:
                        row[j] += dist_val
            else:
                row[i] += remaining

        # Final normalization
        row_sum = sum(row)
        return [x / row_sum for x in row] if row_sum > 0 else [1.0 / len(roles)] * len(roles)

    def to_influence_network(self) -> InfluenceNetwork:
        """
        Convert current agent_states to an InfluenceNetwork for Nemawashi analysis.
        If agent_states is empty, returns a default network.
        """
        if not self.agent_states:
             return InfluenceNetwork(stakeholders=[], matrix=[])

        roles = list(self.agent_states.keys())
        roles.sort()

        stakeholders = [
            Stakeholder(
                name=self.agent_states[role].role.value,
                initial_support=self.agent_states[role].current_opinion,
                stubbornness=self.agent_states[role].degroot_profile.self_confidence
            )
            for role in roles
        ]

        matrix = [self._calculate_row(i, roles, self.agent_states[role]) for i, role in enumerate(roles)]
        return InfluenceNetwork(stakeholders=stakeholders, matrix=matrix)
