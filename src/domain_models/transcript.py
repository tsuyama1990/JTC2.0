import re

from pydantic import BaseModel, ConfigDict, field_validator


class Transcript(BaseModel):
    """
    Represents a raw transcript from user interviews or market reports.
    """
    model_config = ConfigDict(extra="forbid")

    source: str
    content: str
    date: str

    @field_validator("content")
    @classmethod
    def validate_content_length(cls, v: str) -> str:
        """Ensure transcript content is not trivial."""
        if len(v.strip()) < 10:
            msg = "Transcript content is too short."
            raise ValueError(msg)
        return v

    @field_validator("date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        """Ensure date follows YYYY-MM-DD format."""
        pattern = r"^\d{4}-\d{2}-\d{2}$"
        if not re.match(pattern, v):
            msg = "Date must be in YYYY-MM-DD format"
            raise ValueError(msg)
        return v
