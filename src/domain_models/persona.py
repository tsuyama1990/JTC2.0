"""
Defines the Persona domain models.

These models represent the target customer, their demographics,
and their empathy map (Says, Thinks, Does, Feels), critical for
Customer-Problem Fit.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.core.config import get_settings
from src.core.constants import (
    DESC_EMPATHY_DOES,
    DESC_EMPATHY_FEELS,
    DESC_EMPATHY_SAYS,
    DESC_EMPATHY_THINKS,
    DESC_PERSONA_BIO,
    DESC_PERSONA_DEMOGRAPHICS,
    DESC_PERSONA_FRUSTRATIONS,
    DESC_PERSONA_GOALS,
    DESC_PERSONA_NAME,
    DESC_PERSONA_OCCUPATION,
)


class EmpathyMap(BaseModel):
    """
    Represents the Empathy Map of the persona.
    """

    model_config = ConfigDict(extra="forbid")

    says: list[str] = Field(
        ...,
        description=DESC_EMPATHY_SAYS,
        min_length=get_settings().validation.min_list_length,
        max_length=get_settings().validation.max_list_length,
    )
    thinks: list[str] = Field(
        ...,
        description=DESC_EMPATHY_THINKS,
        min_length=get_settings().validation.min_list_length,
        max_length=get_settings().validation.max_list_length,
    )
    does: list[str] = Field(
        ...,
        description=DESC_EMPATHY_DOES,
        min_length=get_settings().validation.min_list_length,
        max_length=get_settings().validation.max_list_length,
    )
    feels: list[str] = Field(
        ...,
        description=DESC_EMPATHY_FEELS,
        min_length=get_settings().validation.min_list_length,
        max_length=get_settings().validation.max_list_length,
    )


class CustomerProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_jobs: list[str] = Field(..., description="Customer jobs and tasks")
    pains: list[str] = Field(..., description="Risks or negative emotions hindering jobs")
    gains: list[str] = Field(..., description="Benefits expected from the jobs")


class ValueMap(BaseModel):
    model_config = ConfigDict(extra="forbid")
    products_and_services: list[str] = Field(..., description="List of main products/services")
    pain_relievers: list[str] = Field(..., description="How it specifically removes customer pain")
    gain_creators: list[str] = Field(..., description="How it specifically creates customer gain")


class ValuePropositionCanvas(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_profile: CustomerProfile
    value_map: ValueMap
    fit_evaluation: str = Field(
        ..., description="Validation of logical fit between relievers/pain and creators/gain"
    )


class MentalTower(BaseModel):
    model_config = ConfigDict(extra="forbid")
    belief: str = Field(
        ..., description="User's underlying beliefs (e.g., 'I don't want to waste time')"
    )
    cognitive_tasks: list[str] = Field(
        ..., description="Tasks/judgements made based on that belief"
    )


class MentalModelDiagram(BaseModel):
    model_config = ConfigDict(extra="forbid")
    towers: list[MentalTower] = Field(..., description="Towers constituting user's thought space")
    feature_alignment: str = Field(..., description="Mapping of how features support the towers")


class Persona(BaseModel):
    """
    Represents the Target Customer Persona.

    Includes demographics, psychographics, and validation status based on primary research.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ...,
        description=DESC_PERSONA_NAME,
        min_length=2,
        max_length=50,
    )
    occupation: str = Field(
        ...,
        description=DESC_PERSONA_OCCUPATION,
        min_length=2,
        max_length=50,
    )
    demographics: str = Field(
        ...,
        description=DESC_PERSONA_DEMOGRAPHICS,
        min_length=5,
        max_length=100,
    )
    goals: list[str] = Field(
        ...,
        description=DESC_PERSONA_GOALS,
        min_length=get_settings().validation.min_list_length,
        max_length=get_settings().validation.max_list_length,
    )
    frustrations: list[str] = Field(
        ...,
        description=DESC_PERSONA_FRUSTRATIONS,
        min_length=get_settings().validation.min_list_length,
        max_length=get_settings().validation.max_list_length,
    )
    bio: str = Field(
        ...,
        description=DESC_PERSONA_BIO,
        min_length=get_settings().validation.min_content_length,
        max_length=get_settings().validation.max_content_length,
    )
    empathy_map: EmpathyMap | None = None

    # New fields for fact-based validation
    is_fact_based: bool = Field(
        default=False,
        description="True if the persona has been validated with primary research (e.g. interviews).",
    )
    interview_insights: list[str] = Field(
        default_factory=list,
        description="Key insights derived from customer interviews.",
        min_length=0,
        max_length=50,
    )

    @field_validator("interview_insights")
    @classmethod
    def validate_insights_content(cls, v: list[str]) -> list[str]:
        """Validate and sanitize content of interview insights."""
        import re

        import bleach  # type: ignore[import-untyped]

        sanitized_insights = []
        for raw_insight in v:
            insight_clean = str(raw_insight).strip()
            if len(insight_clean) < 5:
                msg = f"Insight '{insight_clean}' is too short."
                raise ValueError(msg)
            if len(insight_clean) > 500:
                msg = "Insight is too long."
                raise ValueError(msg)

            # Strict character whitelisting to prevent SQL/Command injection attacks
            # Allow letters, numbers, spaces, common punctuation. Deny SQL/bash special chars like ; ' " %
            if not re.match(r"^[a-zA-Z0-9\s.,!?\-]+$", insight_clean):
                msg = f"Insight contains invalid characters: '{insight_clean}'"
                raise ValueError(msg)

            # Comprehensive sanitization to prevent script/XSS injection
            insight_clean = bleach.clean(insight_clean, tags=[], attributes={}, strip=True)
            sanitized_insights.append(insight_clean)

        return sanitized_insights
