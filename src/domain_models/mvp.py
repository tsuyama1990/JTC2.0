from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class MVPType(StrEnum):
    LANDING_PAGE = "landing_page"
    CONCIERGE = "concierge"
    WIZARD_OF_OZ = "wizard_of_oz"
    SINGLE_FEATURE = "single_feature"


class Feature(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Feature name")
    description: str = Field(..., description="Feature description")
    priority: str = Field(..., description="Must-have, Nice-to-have, etc.")


class MVP(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: MVPType = Field(..., description="Type of MVP")
    core_features: list[Feature] = Field(..., description="List of core features")
    success_criteria: str = Field(..., description="Definition of success")
