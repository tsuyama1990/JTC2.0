from collections.abc import Iterator
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.core.config import get_settings
from src.domain_models.common import LazyIdeaIterator
from src.domain_models.enums import Phase, Role
from src.domain_models.validators import StateValidator

__all__ = ["GlobalState", "Phase"]

from .agent_prompt import AgentPromptSpec
from .alternative_analysis import AlternativeAnalysis
from .customer_journey import CustomerJourney
from .experiment_plan import ExperimentPlan
from .lean_canvas import LeanCanvas
from .mental_model import MentalModelDiagram
from .metrics import Metrics, RingiSho
from .mvp import MVP
from .persona import Persona
from .politics import InfluenceNetwork
from .simulation import AgentState, DialogueMessage
from .sitemap import SitemapAndStory
from .transcript import Transcript
from .value_proposition import ValuePropositionCanvas


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

    # Remastered Phase 2: Customer / Problem Fit
    alternative_analysis: AlternativeAnalysis | None = None
    value_proposition: ValuePropositionCanvas | None = None

    # Remastered Phase 3: Problem / Solution Fit
    mental_model: MentalModelDiagram | None = None
    customer_journey: CustomerJourney | None = None
    sitemap_and_story: SitemapAndStory | None = None

    # Remastered Phase 5 & 6: Output Generation
    agent_prompt_spec: AgentPromptSpec | None = None
    experiment_plan: ExperimentPlan | None = None

    mvp_definition: MVP | None = None
    metrics_data: Metrics | None = None

    debate_history: list[DialogueMessage] = Field(default_factory=list)
    simulation_active: bool = False

    # Updated fields for Cycle 3
    transcripts: list[Transcript] = Field(
        default_factory=list, description="Raw transcripts from PLAUD or interviews"
    )
    rag_index_path: str = Field(
        default_factory=lambda: get_settings().rag.persist_dir,
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
        """Ensure transcripts are unique by source and have valid content."""
        sources = [t.source for t in v]
        if len(sources) != len(set(sources)):
            msg = "Duplicate transcript sources found."
            raise ValueError(msg)

        settings = get_settings()
        for t in v:
            if not t.content or len(t.content.strip()) < settings.validation.min_content_length:
                msg = f"Transcript from {t.source} is too short or empty."
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
            # To validate the elements of a generator without exhausting it entirely,
            # we can peek at the first element if needed, but since it's an Iterator of unknown source,
            # standard Pydantic validation handles element checking if we type it properly,
            # but LazyIdeaIterator abstracts this. We will let LazyIdeaIterator's __next__ handle type checking.
            # But the auditor specifically said: "add type checking to ensure iterator yields LeanCanvas objects".
            # We can wrap it in a checking generator.
            def typed_iterator(it: Iterator[Any]) -> Iterator[LeanCanvas]:
                for item in it:
                    if not isinstance(item, LeanCanvas):
                        msg = f"Iterator must yield LeanCanvas objects, got {type(item)}"
                        raise TypeError(msg)
                    yield item

            return LazyIdeaIterator(typed_iterator(v))

        # Reject invalid types explicitly
        msg = f"generated_ideas must be an Iterator or LazyIdeaIterator, got {type(v)}"
        raise TypeError(msg)

    @model_validator(mode="after")
    def validate_state(self) -> Self:
        """Apply all state validators."""
        StateValidator.validate_phase_requirements(self)
        return self
