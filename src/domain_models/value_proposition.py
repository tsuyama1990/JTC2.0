"""
Value Proposition Canvas models for Problem/Solution fit verification.
"""

from pydantic import BaseModel, ConfigDict, Field

from src.core.config import get_settings


class CustomerProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_jobs: list[str] = Field(
        ...,
        min_length=get_settings().validation.min_list_length,
        description="Jobs and social/emotional tasks the customer wants to get done",
    )
    pains: list[str] = Field(
        ...,
        min_length=get_settings().validation.min_list_length,
        description="Risks and negative emotions that hinder the execution of jobs",
    )
    gains: list[str] = Field(
        ...,
        min_length=get_settings().validation.min_list_length,
        description="Benefits and expectations the customer wants to achieve by executing the job",
    )


class ValueMap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    products_and_services: list[str] = Field(
        ...,
        min_length=get_settings().validation.min_list_length,
        description="List of primary products/services offered",
    )
    pain_relievers: list[str] = Field(
        ...,
        min_length=get_settings().validation.min_list_length,
        description="How exactly to alleviate the customer's Pains",
    )
    gain_creators: list[str] = Field(
        ...,
        min_length=get_settings().validation.min_list_length,
        description="How exactly to create the customer's Gains",
    )


class ValuePropositionCanvas(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_profile: CustomerProfile
    value_map: ValueMap
    fit_evaluation: str = Field(
        ...,
        min_length=get_settings().validation.min_content_length,
        description="Validation result of how logically Pain Relievers fit Pains, and Gain Creators fit Gains",
    )
