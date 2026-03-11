from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.core.config import get_settings


class LeanCanvas(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int
    title: str = Field(..., description="A catchy name for the idea")
    problem: str = Field(..., description="Top 3 problems")
    customer_segments: str = Field(..., description="Target customers")
    unique_value_prop: str = Field(..., description="Single clear compelling message")
    solution: str = Field(..., description="Top 3 features")
    status: str = "draft"

    @field_validator("title")
    @classmethod
    def validate_title_length(cls, v: str) -> str:
        settings = get_settings().validation
        if len(v) < settings.min_title_length:
            msg = f"Title must be at least {settings.min_title_length} characters"
            raise ValueError(msg)
        if len(v) > settings.max_title_length:
            msg = f"Title must be at most {settings.max_title_length} characters"
            raise ValueError(msg)
        return v

    @field_validator("problem", "customer_segments", "unique_value_prop", "solution")
    @classmethod
    def validate_content_length(cls, v: str) -> str:
        if len(v) < 10:
            msg = "Content fields must be at least 10 characters long to ensure detail"
            raise ValueError(msg)
        return v
