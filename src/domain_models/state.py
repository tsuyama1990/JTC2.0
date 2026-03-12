from collections.abc import Iterator
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.domain_models.enums import Phase, Role
from src.domain_models.validators import StateValidator

__all__ = ["GlobalState", "Phase"]

from .agent_spec import AgentPromptSpec
from .alternative import AlternativeAnalysis
from .experiment import ExperimentPlan
from .journey import CustomerJourney
from .lean_canvas import LeanCanvas
from .mental_model import MentalModelDiagram
from .metrics import Metrics, RingiSho
from .mvp import MVP, MVPSpec
from .persona import Persona
from .politics import InfluenceNetwork
from .simulation import AgentState, DialogueMessage
from .sitemap import SitemapAndStory
from .transcript import Transcript
from .value_proposition import ValuePropositionCanvas


class GlobalState(BaseModel):
    """The central state of the LangGraph workflow."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    phase: Phase = Phase.IDEATION
    topic: str = ""

    # Critical: Wrapper for memory efficiency.
    # We use a standard Iterator. Set arbitrary_types_allowed=True to support it.
    generated_ideas: Iterator[LeanCanvas] | None = None

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
        default="",
        description="Path to the local vector store",
    )

    vpc: ValuePropositionCanvas | None = None
    alternative_analysis: AlternativeAnalysis | None = None
    mental_model: MentalModelDiagram | None = None
    customer_journey: CustomerJourney | None = None
    sitemap_and_story: SitemapAndStory | None = None
    experiment_plan: ExperimentPlan | None = None
    agent_prompt_spec: AgentPromptSpec | None = None

    agent_states: dict[Role, AgentState] = Field(
        default_factory=dict, description="Persistent state of agents (e.g. DeGroot weights)"
    )
    influence_network: InfluenceNetwork | None = None
    ringi_sho: RingiSho | None = None

    @field_validator("transcripts")
    @classmethod
    def validate_unique_transcripts(cls, v: list[Transcript]) -> list[Transcript]:
        """Ensure transcripts are unique by source, validate content size, and sanitize."""
        import re

        sources = [t.source for t in v]
        if len(sources) != len(set(sources)):
            msg = "Duplicate transcript sources found."
            raise ValueError(msg)

        for transcript in v:
            if len(transcript.content) > 100000:
                msg = f"Transcript {transcript.source} content exceeds maximum allowed size (100k chars)."
                raise ValueError(msg)
            if len(transcript.content.strip()) < 10:
                msg = f"Transcript {transcript.source} content is too short."
                raise ValueError(msg)

            # Advanced sanitization: strip all HTML tags to prevent XSS
            sanitized = re.sub(r"<[^>]*>", "", transcript.content)
            # Remove null bytes
            sanitized = sanitized.replace("\x00", "")
            # Remove common SQL injection fragments if matched exactly
            sanitized = re.sub(r"(?i)\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|EXEC)\b", "[REDACTED]", sanitized)
            sanitized = sanitized.replace("--", "").replace(";", "")

            if len(sanitized.strip()) < 10:
                msg = f"Transcript {transcript.source} content is too short after sanitization."
                raise ValueError(msg)

            transcript.content = sanitized

        return v

    @field_validator("rag_index_path")
    @classmethod
    def validate_rag_index_path(cls, v: str) -> str:
        import os
        from pathlib import Path

        if not v or not v.strip():
            return v

        is_allowed = False
        allowed_paths = os.getenv("RAG_ALLOWED_PATHS", "data,vector_store,tests,./vector_store").split(",")

        abs_v = str(Path(v).resolve())
        for allowed_path in allowed_paths:
            abs_allowed = str(Path(allowed_path.strip()).resolve())
            try:
                if os.path.commonpath([abs_allowed, abs_v]) == abs_allowed:
                    is_allowed = True
                    break
            except ValueError:
                continue

        if not is_allowed:
            msg = f"Invalid RAG path '{v}'. Must be within allowed paths: {allowed_paths}"
            raise ValueError(msg)

        if not Path(v).exists():
            msg = f"RAG index path '{v}' does not exist."
            raise ValueError(msg)

        return v

    @field_validator("agent_states")
    @classmethod
    def validate_agent_states(cls, v: dict[Role, AgentState]) -> dict[Role, AgentState]:
        """Ensure agent_states keys match the AgentState role."""
        for role, state in v.items():
            if not isinstance(role, Role):
                msg = f"agent_states keys must be Role enums, got {type(role).__name__}"
                raise TypeError(msg)
            if role != state.role:
                msg = f"Key {role} does not match AgentState role {state.role}"
                raise ValueError(msg)
        return v

    @field_validator("generated_ideas", mode="before")
    @classmethod
    def validate_iterator(cls, v: object) -> object:
        """
        Strictly enforces that the input is a valid Iterator.
        """
        if v is None:
            return None

        if isinstance(v, Iterator):
            return v

        # Reject invalid types explicitly
        msg = f"Invalid type for generated_ideas. Expected an Iterator that yields LeanCanvas objects, but got {type(v).__name__} instead. Ensure you are passing a generator or Iterator."
        raise TypeError(msg)

    @model_validator(mode="after")
    def validate_state(self) -> Self:
        """Apply all state validators safely returning verbose context."""
        try:
            StateValidator.validate_phase_requirements(self)
        except ValueError as e:
            msg = f"State Validation Failed: {e}"
            raise ValueError(msg) from e
        return self
