from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator


class Transcript(BaseModel):
    """
    Represents a raw transcript from user interviews or market reports.
    """

    model_config = ConfigDict(extra="forbid")

    source: str
    content: str
    date_recorded: date

    @field_validator("content")
    @classmethod
    def validate_content_length(cls, v: str) -> str:
        """Ensure transcript content is not trivial and analyzes basic structure."""
        cleaned = v.strip()
        if len(cleaned) < 10:
            msg = "Transcript content is too short."
            raise ValueError(msg)
        # basic structural analysis
        if len(cleaned.split()) < 3:
            msg = "Transcript lacks sufficient word count."
            raise ValueError(msg)
        return cleaned
