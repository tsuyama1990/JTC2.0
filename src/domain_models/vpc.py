from pydantic import BaseModel, ConfigDict, Field

from src.core.config import get_settings


class CustomerProfile(BaseModel):
    """
    Represents the Customer Profile portion of the VPC.
    """

    model_config = ConfigDict(extra="forbid")

    customer_jobs: list[str] = Field(
        ...,
        description="List of jobs the customer is trying to get done",
        min_length=get_settings().validation.min_list_length,
        max_length=get_settings().validation.max_list_length,
    )
    pains: list[str] = Field(
        ...,
        description="List of pains experienced by the customer",
        min_length=get_settings().validation.min_list_length,
        max_length=get_settings().validation.max_list_length,
    )
    gains: list[str] = Field(
        ...,
        description="List of gains the customer wants to achieve",
        min_length=get_settings().validation.min_list_length,
        max_length=get_settings().validation.max_list_length,
    )


class ValueMap(BaseModel):
    """
    Represents the Value Map portion of the VPC.
    """

    model_config = ConfigDict(extra="forbid")

    products_and_services: list[str] = Field(
        ...,
        description="List of products and services offered",
        min_length=get_settings().validation.min_list_length,
        max_length=get_settings().validation.max_list_length,
    )
    pain_relievers: list[str] = Field(
        ...,
        description="How the products/services relieve pains",
        min_length=get_settings().validation.min_list_length,
        max_length=get_settings().validation.max_list_length,
    )
    gain_creators: list[str] = Field(
        ...,
        description="How the products/services create gains",
        min_length=get_settings().validation.min_list_length,
        max_length=get_settings().validation.max_list_length,
    )


class ValuePropositionCanvas(BaseModel):
    """
    Value Proposition Canvas Model. Maps Customer Profile to Value Map.
    """

    model_config = ConfigDict(extra="forbid")

    profile: CustomerProfile = Field(..., description="The Customer Profile")
    map: ValueMap = Field(..., description="The Value Map")
    fit_evaluation: str = Field(
        ...,
        description="A string confirming logical alignment (fit) between profile and map",
        min_length=10,
        max_length=1000,
    )
