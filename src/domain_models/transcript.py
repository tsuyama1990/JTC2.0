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
