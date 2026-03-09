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


from typing import Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class EmpathyMap(BaseModel):
    """
    Represents the Empathy Map of the persona.
    """

    model_config = ConfigDict(extra="forbid")

    says: list[str] = Field(..., description=DESC_EMPATHY_SAYS)
    thinks: list[str] = Field(..., description=DESC_EMPATHY_THINKS)
    does: list[str] = Field(..., description=DESC_EMPATHY_DOES)
    feels: list[str] = Field(..., description=DESC_EMPATHY_FEELS)

    @model_validator(mode="after")
    def validate_lengths(self) -> Self:
        settings = get_settings()
        min_len = settings.validation.min_list_length
        max_len = settings.validation.max_list_length
        for field in ["says", "thinks", "does", "feels"]:
            val = getattr(self, field)
            if len(val) < min_len:
                msg = f"{field} must have at least {min_len} items"
                raise ValueError(msg)
            if len(val) > max_len:
                msg = f"{field} must have at most {max_len} items"
                raise ValueError(msg)
        return self


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
    )
    frustrations: list[str] = Field(
        ...,
        description=DESC_PERSONA_FRUSTRATIONS,
    )
    bio: str = Field(
        ...,
        description=DESC_PERSONA_BIO,
    )

    @model_validator(mode="after")
    def validate_lengths(self) -> Self:
        settings = get_settings()

        # List field validation
        min_list_len = settings.validation.min_list_length
        max_list_len = settings.validation.max_list_length
        for field in ["goals", "frustrations"]:
            val = getattr(self, field)
            if len(val) < min_list_len:
                msg = f"{field} must have at least {min_list_len} items"
                raise ValueError(msg)
            if len(val) > max_list_len:
                msg = f"{field} must have at most {max_list_len} items"
                raise ValueError(msg)

        # Content validation
        min_content_len = settings.validation.min_content_length
        max_content_len = settings.validation.max_content_length
        if len(self.bio) < min_content_len:
            msg = f"bio must be at least {min_content_len} characters"
            raise ValueError(msg)
        if len(self.bio) > max_content_len:
            msg = f"bio must be at most {max_content_len} characters"
            raise ValueError(msg)

        return self
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
