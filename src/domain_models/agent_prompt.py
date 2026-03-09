"""
Agent Prompt Specification models.
"""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.core.config import SettingsFactory
from src.domain_models.sitemap import UserStory


class StateMachine(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success: str = Field(
        ...,
        description="Complete layout when data is normal",
    )
    loading: str = Field(
        ...,
        description="Waiting UI using Skeleton components",
    )
    error: str = Field(
        ...,
        description="Placement of fallback UI and Retry button",
    )
    empty: str = Field(
        ...,
        description="Empty State including CTA when data is 0",
    )

    @model_validator(mode="after")
    def validate_lengths(self) -> Self:
        settings = SettingsFactory().build()
        for field in ["success", "loading", "error", "empty"]:
            val = getattr(self, field)
            if isinstance(val, str) and len(val) < settings.validation.min_content_length:
                msg = (
                    f"{field} must be at least {settings.validation.min_content_length} characters"
                )
                raise ValueError(msg)
        return self


class AgentPromptSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sitemap: str = Field(
        ...,
        description="Overall routing and information architecture of the app",
    )
    routing_and_constraints: str = Field(
        ...,
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
        description="Zod schema and edge case requirements",
    )
    mermaid_flowchart: str = Field(
        ...,
        description="State transition and data flow diagram using Mermaid syntax",
    )

    @model_validator(mode="after")
    def validate_lengths(self) -> Self:
        settings = SettingsFactory().build()
        for field in [
            "sitemap",
            "routing_and_constraints",
            "validation_rules",
            "mermaid_flowchart",
        ]:
            val = getattr(self, field)
            if isinstance(val, str) and len(val) < settings.validation.min_content_length:
                msg = (
                    f"{field} must be at least {settings.validation.min_content_length} characters"
                )
                raise ValueError(msg)
        return self
