from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from .lean_canvas import LeanCanvas


class Phase(StrEnum):
    IDEATION = "ideation"
    VERIFICATION = "verification"
    SOLUTION = "solution"
    PMF = "pmf"


class GlobalState(BaseModel):
    """The central state of the LangGraph workflow."""

    model_config = ConfigDict(extra="forbid")

    phase: Phase = Phase.IDEATION
    topic: str = ""
    generated_ideas: list[LeanCanvas] = []
    selected_idea: LeanCanvas | None = None
    messages: list[str] = []
