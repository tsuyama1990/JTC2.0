from pydantic import BaseModel, ConfigDict, Field


class CustomerProfile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_jobs: list[str] = Field(..., min_length=1)
    pains: list[str] = Field(..., min_length=1)
    gains: list[str] = Field(..., min_length=1)


class ValueMap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    products_and_services: list[str] = Field(..., min_length=1)
    pain_relievers: list[str] = Field(..., min_length=1)
    gain_creators: list[str] = Field(..., min_length=1)


class ValuePropositionCanvas(BaseModel):
    model_config = ConfigDict(extra="forbid")

    customer_profile: CustomerProfile
    value_map: ValueMap
    fit_evaluation: str = Field(..., min_length=10)
