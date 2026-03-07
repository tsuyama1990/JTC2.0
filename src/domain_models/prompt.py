from pydantic import BaseModel, ConfigDict, Field

from src.domain_models.sitemap import SitemapAndStory, UserStory


class StateMachine(BaseModel):
    model_config = ConfigDict(extra="forbid")

    success_state: str = Field(..., min_length=5)
    loading_state: str = Field(..., min_length=5)
    error_state: str = Field(..., min_length=5)
    empty_state: str = Field(..., min_length=5)


class AgentPromptSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sitemap: SitemapAndStory
    routing_constraints: list[str] = Field(..., min_length=1)
    core_user_story: UserStory
    state_machine: StateMachine
    validation_rules: list[str] = Field(..., min_length=1)
    mermaid_flowchart: str = Field(..., min_length=10)
