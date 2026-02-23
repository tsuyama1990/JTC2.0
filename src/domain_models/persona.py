from pydantic import BaseModel, ConfigDict, Field

from src.core.config import settings
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
    model_config = ConfigDict(extra="forbid")

    says: list[str] = Field(
        ...,
        description=DESC_EMPATHY_SAYS,
        min_length=settings.validation.min_list_length,
        max_length=settings.validation.max_list_length,
    )
    thinks: list[str] = Field(
        ...,
        description=DESC_EMPATHY_THINKS,
        min_length=settings.validation.min_list_length,
        max_length=settings.validation.max_list_length,
    )
    does: list[str] = Field(
        ...,
        description=DESC_EMPATHY_DOES,
        min_length=settings.validation.min_list_length,
        max_length=settings.validation.max_list_length,
    )
    feels: list[str] = Field(
        ...,
        description=DESC_EMPATHY_FEELS,
        min_length=settings.validation.min_list_length,
        max_length=settings.validation.max_list_length,
    )


class Persona(BaseModel):
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
        min_length=settings.validation.min_list_length,
        max_length=settings.validation.max_list_length,
    )
    frustrations: list[str] = Field(
        ...,
        description=DESC_PERSONA_FRUSTRATIONS,
        min_length=settings.validation.min_list_length,
        max_length=settings.validation.max_list_length,
    )
    bio: str = Field(
        ...,
        description=DESC_PERSONA_BIO,
        min_length=settings.validation.min_content_length,
        max_length=settings.validation.max_content_length,
    )
    empathy_map: EmpathyMap | None = None
