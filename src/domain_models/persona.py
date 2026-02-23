from pydantic import BaseModel, ConfigDict, Field


class EmpathyMap(BaseModel):
    model_config = ConfigDict(extra="forbid")

    says: list[str] = Field(..., description="What the customer says")
    thinks: list[str] = Field(..., description="What the customer thinks")
    does: list[str] = Field(..., description="What the customer does")
    feels: list[str] = Field(..., description="What the customer feels")


class Persona(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., description="Name of the persona")
    occupation: str = Field(..., description="Job title or role")
    demographics: str = Field(..., description="Age, gender, location, etc.")
    goals: list[str] = Field(..., description="What they want to achieve")
    frustrations: list[str] = Field(..., description="Pain points and obstacles")
    bio: str = Field(..., description="Short biography")
    empathy_map: EmpathyMap | None = None
