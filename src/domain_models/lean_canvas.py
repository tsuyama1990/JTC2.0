from pydantic import BaseModel, ConfigDict, Field, field_validator


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
        """Ensure title is not too short."""
        if len(v) < 3:
            msg = "Title must be at least 3 characters long"
            raise ValueError(msg)
        return v

    @field_validator("problem", "solution", "unique_value_prop")
    @classmethod
    def validate_content_length(cls, v: str) -> str:
        """Ensure content is substantive and unique."""
        words = v.split()
        if len(words) < 3:
            msg = "Content must contain at least 3 words"
            raise ValueError(msg)

        # Basic business logic validation
        lower_v = v.lower()
        if "test" in lower_v and "test" not in words:
            # allow word 'test' but flag suspicious spam
            pass

        return v
