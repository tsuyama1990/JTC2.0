from pydantic import BaseModel, ConfigDict, Field

from src.core.config import get_settings


class CustomerProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_jobs: list[str] = Field(..., min_length=get_settings().validation.min_content_length)
    pains: list[str] = Field(..., min_length=get_settings().validation.min_content_length)
    gains: list[str] = Field(..., min_length=get_settings().validation.min_content_length)


class ValueMap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    products_and_services: list[str] = Field(
        ..., min_length=get_settings().validation.min_content_length
    )
    pain_relievers: list[str] = Field(..., min_length=get_settings().validation.min_content_length)
    gain_creators: list[str] = Field(..., min_length=get_settings().validation.min_content_length)


class ValuePropositionCanvas(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_profile: CustomerProfile
    value_map: ValueMap
    fit_evaluation: str = Field(..., min_length=get_settings().validation.min_title_length)
