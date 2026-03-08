from pydantic import BaseModel, ConfigDict, Field

from src.core.config import get_settings

from .sitemap import Route, UserStory


class StateMachine(BaseModel):
    """
    Defines layout states for success, loading, error, and empty.
    """

    model_config = ConfigDict(extra="forbid")

    success: str = Field(
        ...,
        description="Layout for success state",
        min_length=10,
        max_length=500,
    )
    loading: str = Field(
        ...,
        description="Layout for loading state",
        min_length=10,
        max_length=500,
    )
    error: str = Field(
        ...,
        description="Layout for error state",
        min_length=10,
        max_length=500,
    )
    empty: str = Field(
        ...,
        description="Layout for empty state",
        min_length=10,
        max_length=500,
    )


class AgentPromptSpec(BaseModel):
    """
    Agent Prompt Spec Model. The perfect markdown prompt for AI coding tools.
    """

    model_config = ConfigDict(extra="forbid")

    sitemap: list[Route] = Field(
        ...,
        description="The sitemap outlining URLs and transitions",
        min_length=get_settings().validation.min_list_length,
        max_length=get_settings().validation.max_list_length,
    )
    routing_and_constraints: str = Field(
        ...,
        description="Constraints and specific routing behavior",
        min_length=10,
        max_length=1000,
    )
    core_user_story: UserStory = Field(
        ...,
        description="The core user story to fulfill",
    )
    state_machine: StateMachine = Field(
        ...,
        description="The layout state definitions",
    )
    validation_rules: list[str] = Field(
        ...,
        description="List of required validation rules",
        min_length=get_settings().validation.min_list_length,
        max_length=get_settings().validation.max_list_length,
    )
    mermaid_flowchart: str = Field(
        ...,
        description="The mermaid flowchart definition of the state machine",
        min_length=10,
        max_length=2000,
    )
