from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.core.constants import DEFAULT_MAX_TITLE_LENGTH, DEFAULT_MIN_TITLE_LENGTH


class CanvasStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"


class LeanCanvas(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int
    title: str = Field(..., description="A catchy name for the idea")
    problem: str = Field(..., description="Top 3 problems")
    customer_segments: str = Field(..., description="Target customers")
    unique_value_prop: str = Field(..., description="Single clear compelling message")
    solution: str = Field(..., description="Top 3 features")
    status: CanvasStatus = CanvasStatus.DRAFT

    @field_validator("title")
    @classmethod
    def validate_title_length(cls, v: str) -> str:
        # Avoid relying on dynamic UI settings for validation bounds
        if len(v) < DEFAULT_MIN_TITLE_LENGTH:
            msg = f"Title must be at least {DEFAULT_MIN_TITLE_LENGTH} characters"
            raise ValueError(msg)
        if len(v) > DEFAULT_MAX_TITLE_LENGTH:
            msg = f"Title must be at most {DEFAULT_MAX_TITLE_LENGTH} characters"
            raise ValueError(msg)
        return v

    @field_validator("problem", "customer_segments", "unique_value_prop", "solution")
    @classmethod
    def validate_content_length(cls, v: str) -> str:
        if len(v) < 10:
            msg = "Content fields must be at least 10 characters long to ensure detail"
            raise ValueError(msg)
        return v
