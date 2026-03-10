"""
Defines the Minimum Viable Product (MVP) domain models.

This module encapsulates the structure of the MVP, including its type, core features,
and success criteria, following the 'Lean Startup' methodology.
"""

import re
from enum import StrEnum

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator

from src.core.config import get_settings
from src.core.constants import (
    DESC_FEATURE_DESC,
    DESC_FEATURE_NAME,
    DESC_FEATURE_PRIORITY,
    DESC_MVP_CORE_FEATURES,
    DESC_MVP_SUCCESS_CRITERIA,
    DESC_MVP_TYPE,
)

# Pre-compiled regex pattern at module level
# Allow alphanumeric only, length 1-50
# Deny special chars often used in injection: < > ; & ' "
# Use parameterized queries for database operations to prevent SQL injection.
COMPONENT_PATTERN = re.compile(r"^[a-zA-Z0-9]{1,50}$")


class AlternativeTool(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(..., description="Name of alternative (e.g., Excel, SaaS)")
    financial_cost: str = Field(..., description="Financial cost")
    time_cost: str = Field(..., description="Time cost")
    ux_friction: str = Field(..., description="Maximum stress/friction felt by user")


class AlternativeAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_alternatives: list[AlternativeTool]
    switching_cost: str = Field(..., description="Cost/effort required to switch")
    ten_x_value: str = Field(..., description="10x value overcoming switching costs (UVP)")


class JourneyPhase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phase_name: str = Field(..., description="Phase name (e.g., Awareness, Consideration)")
    touchpoint: str = Field(..., description="Contact point with system/environment")
    customer_action: str = Field(..., description="Specific action taken")
    mental_tower_ref: str = Field(..., description="Belief underlying this action")
    pain_points: list[str] = Field(..., description="Pain felt in this phase")
    emotion_score: int = Field(..., ge=-5, le=5, description="Emotional fluctuation (-5 to 5)")


class CustomerJourney(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phases: list[JourneyPhase] = Field(..., min_length=3, max_length=7)
    worst_pain_phase: str = Field(..., description="Phase with deepest pain to solve")


class Route(BaseModel):
    model_config = ConfigDict(extra="forbid")
    path: str = Field(..., description="URL path (e.g., /, /login)")
    name: str = Field(..., description="Page name")
    purpose: str = Field(..., description="Purpose of page")
    is_protected: bool = Field(..., description="Requires auth?")


class UserStory(BaseModel):
    model_config = ConfigDict(extra="forbid")
    as_a: str = Field(..., description="Persona")
    i_want_to: str = Field(..., description="Action")
    so_that: str = Field(..., description="Goal/Value")
    acceptance_criteria: list[str] = Field(..., description="Acceptance criteria")
    target_route: str = Field(..., description="Main URL path for this action")


class SitemapAndStory(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sitemap: list[Route] = Field(..., description="Overall routing structure")
    core_story: UserStory = Field(..., description="Most critical story to validate as MVP")


class StateMachine(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: str = Field(..., description="Complete layout for normal data")
    loading: str = Field(..., description="Waiting UI using Skeleton")
    error: str = Field(..., description="Fallback UI and Retry button")
    empty: str = Field(..., description="Empty state with CTA")


class AgentPromptSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sitemap: str = Field(..., description="Routing and information architecture")
    routing_and_constraints: str = Field(..., description="SSR/Client bounds, UI library limits")
    core_user_story: UserStory
    state_machine: StateMachine
    validation_rules: str = Field(..., description="Zod schema or edge cases")
    mermaid_flowchart: str = Field(..., description="State/Data flow diagram in Mermaid")


class MVPType(StrEnum):
    LANDING_PAGE = "landing_page"
    CONCIERGE = "concierge"
    WIZARD_OF_OZ = "wizard_of_oz"
    SINGLE_FEATURE = "single_feature"


class Priority(StrEnum):
    MUST_HAVE = "must_have"
    SHOULD_HAVE = "should_have"
    COULD_HAVE = "could_have"
    WONT_HAVE = "wont_have"


class DeploymentStatus(StrEnum):
    PENDING = "pending"
    DEPLOYED = "deployed"
    FAILED = "failed"


class Feature(BaseModel):
    """
    Represents a single feature of the MVP.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description=DESC_FEATURE_NAME, min_length=3, max_length=50)
    description: str = Field(
        ...,
        description=DESC_FEATURE_DESC,
        min_length=get_settings().validation.min_content_length,
        max_length=200,
    )
    priority: Priority = Field(..., description=DESC_FEATURE_PRIORITY)


class MVP(BaseModel):
    """
    Represents the Business Definition of the MVP.

    This is the primary output of Gate 3 (Problem-Solution Fit).
    It defines 'WHAT' to build (features, type) and 'WHY' (success criteria).

    Attributes:
        type: The type of MVP (e.g. Landing Page).
        core_features: List of must-have features.
        success_criteria: How success is measured.
        v0_url: Link to the generated UI (filled in Cycle 5).
    """

    model_config = ConfigDict(extra="forbid")

    type: MVPType = Field(..., description=DESC_MVP_TYPE)
    core_features: list[Feature] = Field(
        ...,
        description=DESC_MVP_CORE_FEATURES,
        min_length=get_settings().validation.min_list_length,
    )
    success_criteria: str = Field(
        ...,
        description=DESC_MVP_SUCCESS_CRITERIA,
        min_length=get_settings().validation.min_content_length,
        max_length=500,
    )

    # New fields for v0.dev integration
    # Changed to AnyHttpUrl for validation of http/https
    v0_url: AnyHttpUrl | None = Field(
        default=None,
        description="URL of the deployed MVP on v0.dev",
    )

    @field_validator("v0_url")
    @classmethod
    def validate_v0_url(cls, v: AnyHttpUrl | None) -> AnyHttpUrl | None:
        """Ensure the URL belongs to the allowed v0.dev domain."""
        if v is not None:
            if v.scheme not in ("http", "https"):
                msg = f"Invalid URL scheme: {v.scheme}. Only http/https are allowed."
                raise ValueError(msg)
            if v.host not in ("v0.dev", "api.v0.dev"):
                msg = f"Invalid URL domain: {v.host}. Only v0.dev is allowed."
                raise ValueError(msg)
        return v
    deployment_status: DeploymentStatus = Field(
        default=DeploymentStatus.PENDING,
        description="Status of the MVP deployment (e.g., pending, deployed, failed)",
    )


class MVPSpec(BaseModel):
    """
    Technical Specification for MVP Generation (v0.dev).

    This is the input for Cycle 5 (MVP Generation).
    It defines 'HOW' the UI should be generated by the AI tool.

    Attributes:
        app_name: Name of the application.
        core_feature: The specific core feature to focus on (One Feature principle).
        ui_style: Visual style instructions.
        v0_prompt: The actual prompt sent to v0.dev API.
    """

    model_config = ConfigDict(extra="forbid")

    app_name: str = Field(..., description="Name of the application", min_length=1, max_length=50)
    core_feature: str = Field(
        ..., description="The single core feature to implement", min_length=10
    )
    ui_style: str = Field(default="Modern, Clean, Corporate", description="Visual style of the UI")
    v0_prompt: str | None = Field(
        default=None,
        description="The prompt used to generate the UI via v0.dev",
        min_length=1,
        max_length=1000,
    )
    components: list[str] = Field(
        default_factory=lambda: ["Hero Section", "Feature Demo", "Call to Action"],
        description="Key UI components to include",
        max_length=20,  # Security: Limit max components to prevent memory exhaustion
    )

    @field_validator("components")
    @classmethod
    def validate_components(cls, v: list[str]) -> list[str]:
        """Validate component names to prevent injection/malformed input."""
        for comp in v:
            if len(comp) > 50:
                msg = f"Component name too long: {comp}"
                raise ValueError(msg)
            if not COMPONENT_PATTERN.match(comp):
                msg = f"Invalid component name: {comp}. Must be alphanumeric/safe chars only."
                raise ValueError(msg)
        return v

    @field_validator("v0_prompt")
    @classmethod
    def validate_v0_prompt(cls, v: str | None) -> str | None:
        """Ensure v0_prompt is non-empty if provided and sanitize it."""
        if v is not None:
            v = v.strip()
            if not v:
                msg = "v0_prompt must be a non-empty string if provided."
                raise ValueError(msg)
            # Basic sanitization to remove script tags
            v = re.sub(r"<script.*?>.*?</script>", "", v, flags=re.IGNORECASE | re.DOTALL)
        return v
