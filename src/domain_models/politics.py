from pydantic import BaseModel, ConfigDict, Field


class Stakeholder(BaseModel):
    """
    Represents an agent in the influence network.
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    initial_support: float = Field(..., ge=0.0, le=1.0)
    stubbornness: float = Field(..., ge=0.0, le=1.0)


class InfluenceNetwork(BaseModel):
    """
    Represents the influence network for the DeGroot model.
    """

    model_config = ConfigDict(extra="forbid")

    stakeholders: list[Stakeholder]
    matrix: list[list[float]]  # Row-stochastic matrix W
