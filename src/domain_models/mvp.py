"""
Defines the Minimum Viable Product (MVP) domain models.

This module encapsulates the structure of the MVP, including its type, core features,
and success criteria, following the 'Lean Startup' methodology.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from src.core.config import get_settings
from src.core.constants import (
    DESC_FEATURE_DESC,
    DESC_FEATURE_NAME,
    DESC_FEATURE_PRIORITY,
    DESC_MVP_CORE_FEATURES,
    DESC_MVP_SUCCESS_CRITERIA,
    DESC_MVP_TYPE,
)


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
    Represents the MVP definition.

    Attributes:
        type: The type of MVP (e.g. Landing Page).
        core_features: List of must-have features.
        success_criteria: How success is measured.
        v0_url: Integration with v0.dev for UI generation.
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
    # Changed to HttpUrl for validation
    v0_url: HttpUrl | None = Field(
        default=None,
        description="URL of the deployed MVP on v0.dev",
    )
    deployment_status: DeploymentStatus = Field(
        default=DeploymentStatus.PENDING,
        description="Status of the MVP deployment (e.g., pending, deployed, failed)",
    )
