"""
Agent Prompt Specification models.
"""

from pydantic import BaseModel, ConfigDict, Field

from src.core.config import get_settings
from src.domain_models.sitemap import UserStory


class StateMachine(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="Complete layout when data is normal",
    )
    loading: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="Waiting UI using Skeleton components",
    )
    error: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="Placement of fallback UI and Retry button",
    )
    empty: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="Empty State including CTA when data is 0",
    )


class AgentPromptSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sitemap: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="Overall routing and information architecture of the app",
    )
    routing_and_constraints: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="Boundaries of SSR/Client Components, UI library specifications",
    )
    core_user_story: UserStory = Field(
        ...,
        description="The core user story details",
    )
    state_machine: StateMachine = Field(
        ...,
        description="State machine mapping",
    )
    validation_rules: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="Zod schema and edge case requirements",
    )
    mermaid_flowchart: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="State transition and data flow diagram using Mermaid syntax",
    )
