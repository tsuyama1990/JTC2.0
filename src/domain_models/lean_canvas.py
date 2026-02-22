from pydantic import BaseModel, ConfigDict, Field


class LeanCanvas(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    title: str = Field(..., description="A catchy name for the idea")
    problem: str = Field(..., description="Top 3 problems")
    customer_segments: str = Field(..., description="Target customers")
    unique_value_prop: str = Field(..., description="Single clear compelling message")
    solution: str = Field(..., description="Top 3 features")
    status: str = "draft"
