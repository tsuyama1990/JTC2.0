"""
Defines the Persona domain models.

These models represent the target customer, their demographics,
and their empathy map (Says, Thinks, Does, Feels), critical for
Customer-Problem Fit.
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator

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
        min_length=1,
        max_length=20,
    )
    thinks: list[str] = Field(
        ...,
        description=DESC_EMPATHY_THINKS,
        min_length=1,
        max_length=20,
    )
    does: list[str] = Field(
        ...,
        description=DESC_EMPATHY_DOES,
        min_length=1,
        max_length=20,
    )
    feels: list[str] = Field(
        ...,
        description=DESC_EMPATHY_FEELS,
        min_length=1,
        max_length=20,
    )


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
        min_length=1,
        max_length=20,
    )
    frustrations: list[str] = Field(
        ...,
        description=DESC_PERSONA_FRUSTRATIONS,
        min_length=1,
        max_length=20,
    )
    bio: str = Field(
        ...,
        description=DESC_PERSONA_BIO,
        min_length=3,
        max_length=1000,
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
        max_length=50,  # Added max length limit
    )

    @field_validator("interview_insights")
    @classmethod
    def validate_insights_content(cls, v: list[str]) -> list[str]:
        """Validate content of interview insights."""
        for insight in v:
            if len(insight.strip()) < 5:
                msg = f"Insight '{insight}' is too short."
                raise ValueError(msg)
        return v
