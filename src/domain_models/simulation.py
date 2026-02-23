from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Role(StrEnum):
    """Roles in the simulation."""

    NEW_EMPLOYEE = "New Employee"
    FINANCE = "Finance Manager"
    SALES = "Sales Manager"
    CPO = "CPO"


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
