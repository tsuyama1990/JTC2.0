from pydantic import BaseModel, ConfigDict, Field

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
    VAL_MAX_CONTENT_LENGTH,
    VAL_MIN_CONTENT_LENGTH,
)


class EmpathyMap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    says: list[str] = Field(..., description=DESC_EMPATHY_SAYS, min_length=1)
    thinks: list[str] = Field(..., description=DESC_EMPATHY_THINKS, min_length=1)
    does: list[str] = Field(..., description=DESC_EMPATHY_DOES, min_length=1)
    feels: list[str] = Field(..., description=DESC_EMPATHY_FEELS, min_length=1)


class Persona(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description=DESC_PERSONA_NAME, min_length=2, max_length=50)
    occupation: str = Field(
        ..., description=DESC_PERSONA_OCCUPATION, min_length=2, max_length=50
    )
    demographics: str = Field(
        ..., description=DESC_PERSONA_DEMOGRAPHICS, min_length=5, max_length=100
    )
    goals: list[str] = Field(..., description=DESC_PERSONA_GOALS, min_length=1)
    frustrations: list[str] = Field(..., description=DESC_PERSONA_FRUSTRATIONS, min_length=1)
    bio: str = Field(
        ...,
        description=DESC_PERSONA_BIO,
        min_length=VAL_MIN_CONTENT_LENGTH,
        max_length=VAL_MAX_CONTENT_LENGTH,
    )
    empathy_map: EmpathyMap | None = None
