"""
Value Proposition Canvas models for Problem/Solution fit verification.
"""

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator




class CustomerProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_jobs: list[str] = Field(
        ...,
        description="Jobs and social/emotional tasks the customer wants to get done",
    )
    pains: list[str] = Field(
        ...,
        description="Risks and negative emotions that hinder the execution of jobs",
    )
    gains: list[str] = Field(
        ...,
        description="Benefits and expectations the customer wants to achieve by executing the job",
    )

    @model_validator(mode="after")
    def validate_lengths(self) -> Self:
        for field in ["customer_jobs", "pains", "gains"]:
            val = getattr(self, field)
            if isinstance(val, list) and len(val) < 1:
                msg = f"{field} must contain at least {1} items"
                raise ValueError(msg)
        return self


class ValueMap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    products_and_services: list[str] = Field(
        ...,
        description="List of primary products/services offered",
    )
    pain_relievers: list[str] = Field(
        ...,
        description="How exactly to alleviate the customer's Pains",
    )
    gain_creators: list[str] = Field(
        ...,
        description="How exactly to create the customer's Gains",
    )

    @model_validator(mode="after")
    def validate_lengths(self) -> Self:
        for field in ["products_and_services", "pain_relievers", "gain_creators"]:
            val = getattr(self, field)
            if isinstance(val, list) and len(val) < 1:
                msg = f"{field} must contain at least {1} items"
                raise ValueError(msg)
        return self


class ValuePropositionCanvas(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_profile: CustomerProfile
    value_map: ValueMap
    fit_evaluation: str = Field(
        ...,
        description="Validation result of how logically Pain Relievers fit Pains, and Gain Creators fit Gains",
    )

    @model_validator(mode="after")
    def validate_lengths(self) -> Self:
        return self
