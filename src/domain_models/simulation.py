from pydantic import BaseModel, ConfigDict, Field

from src.domain_models.enums import Role

__all__ = ["AgentState", "DeGrootProfile", "DialogueMessage", "Role"]


class DeGrootProfile(BaseModel):
    """
    Parameters for the DeGroot opinion dynamics model.

    Attributes:
        self_confidence (w_ii): How much the agent trusts their own opinion (0.0 to 1.0).
        influence_weights (w_ij): Weights assigned to other agents' opinions. Key is the Role value.
    """

    model_config = ConfigDict(extra="forbid")

    self_confidence: float = Field(0.5, ge=0.0, le=1.0)
    influence_weights: dict[str, float] = Field(default_factory=dict)


class AgentState(BaseModel):
    """
    State of an agent in the simulation.
    """

    model_config = ConfigDict(extra="forbid")

    role: Role
    degroot_profile: DeGrootProfile = Field(default_factory=DeGrootProfile)


class DialogueMessage(BaseModel):
    """
    A single message in the debate simulation.

    Attributes:
        role: The role of the speaker.
        content: The content of the message.
        timestamp: The timestamp of the message (simulation time or sequence).
    """

    model_config = ConfigDict(extra="forbid")

    role: Role
    content: str = Field(min_length=1)
    timestamp: float
