from functools import lru_cache
from typing import ClassVar, Self

from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.constants import (
    ERR_CONFIG_MISSING_OPENAI_KEY,
    ERR_CONFIG_MISSING_TAVILY_KEY,
    ERR_INVALID_COLOR,
    ERR_INVALID_DIMENSIONS,
    ERR_INVALID_FPS,
    ERR_INVALID_METRIC_KEY,
    ERR_INVALID_RESOLUTION,
    ERR_LLM_CONFIG_MISSING,
    ERR_LLM_FAILURE,
    ERR_MISSING_MVP,
    ERR_MISSING_PERSONA,
    ERR_SEARCH_CONFIG_MISSING,
    ERR_SEARCH_FAILED,
    ERR_TOO_MANY_METRICS,
    ERR_UNIQUE_ID_VIOLATION,
    MSG_CYCLE_COMPLETE,
    MSG_EXECUTION_ERROR,
    MSG_GENERATED_HEADER,
    MSG_ID_NOT_FOUND,
    MSG_INVALID_INPUT,
    MSG_NO_IDEAS,
    MSG_PHASE_START,
    MSG_PRESS_ENTER,
    MSG_RESEARCHING,
    MSG_SELECT_PROMPT,
    MSG_SELECTED,
    MSG_SIM_TITLE,
    MSG_TOPIC_EMPTY,
    MSG_WAIT,
    MSG_WAITING_FOR_DEBATE,
)


class ValidationConfig(BaseSettings):
    """Validation constraints for domain models."""

    # Title & Content
    min_title_length: int = 3
    max_title_length: int = 100
    min_content_length: int = 3
    max_content_length: int = 1000

    # Lists
    min_list_length: int = 1
    max_list_length: int = 20

    # Metrics
    max_custom_metrics: int = 50
    min_metric_value: float = 0.0
    max_percentage_value: float = 100.0


class ErrorMessages(BaseSettings):
    """Error messages for the application."""

    unique_id_violation: str = ERR_UNIQUE_ID_VIOLATION
    config_missing_openai: str = ERR_CONFIG_MISSING_OPENAI_KEY
    config_missing_tavily: str = ERR_CONFIG_MISSING_TAVILY_KEY
    search_config_missing: str = ERR_SEARCH_CONFIG_MISSING
    llm_config_missing: str = ERR_LLM_CONFIG_MISSING
    search_failed: str = ERR_SEARCH_FAILED
    llm_failure: str = ERR_LLM_FAILURE

    # Validation Errors
    too_many_metrics: str = ERR_TOO_MANY_METRICS
    invalid_metric_key: str = ERR_INVALID_METRIC_KEY
    missing_persona: str = ERR_MISSING_PERSONA
    missing_mvp: str = ERR_MISSING_MVP


class UIConfig(BaseSettings):
    """UI Strings and Configuration."""

    # Load from env var "UI_PAGE_SIZE", default to 5
    page_size: int = Field(alias="UI_PAGE_SIZE", default=5)

    # Messages
    no_ideas: str = MSG_NO_IDEAS
    generated_header: str = MSG_GENERATED_HEADER
    press_enter: str = MSG_PRESS_ENTER
    select_prompt: str = MSG_SELECT_PROMPT
    id_not_found: str = MSG_ID_NOT_FOUND
    invalid_input: str = MSG_INVALID_INPUT
    selected: str = MSG_SELECTED
    cycle_complete: str = MSG_CYCLE_COMPLETE
    topic_empty: str = MSG_TOPIC_EMPTY
    phase_start: str = MSG_PHASE_START
    researching: str = MSG_RESEARCHING
    wait: str = MSG_WAIT
    execution_error: str = MSG_EXECUTION_ERROR


class AgentConfig(BaseModel):
    """Configuration for a single agent in the UI."""

    role: str
    label: str
    color: int
    x: int
    y: int
    w: int
    h: int
    text_x: int
    text_y: int

    @field_validator("color")
    @classmethod
    def validate_color(cls, v: int) -> int:
        """Ensure color is within Pyxel palette (0-15)."""
        if not (0 <= v <= 15):
            raise ValueError(ERR_INVALID_COLOR)
        return v

    @field_validator("w", "h")
    @classmethod
    def validate_dimensions(cls, v: int) -> int:
        """Ensure dimensions are positive."""
        if v <= 0:
            raise ValueError(ERR_INVALID_DIMENSIONS)
        return v


def _load_default_agents_config() -> dict[str, AgentConfig]:
    """Load default agent configuration."""
    # Defined explicitly within the function to avoid global module-level mutable state
    # while adhering to the requirement of no hardcoded settings in 'global scope'.
    # In a real production system, this could load from an external JSON/YAML.
    # The default factory allows this to be overridden by a Pydantic environment variable source.
    return {
        "New Employee": AgentConfig(
            role="New Employee",
            label="NewEmp",
            color=11,
            x=20,
            y=80,
            w=20,
            h=30,
            text_x=15,
            text_y=112,
        ),
        "Finance Manager": AgentConfig(
            role="Finance Manager",
            label="Finance",
            color=8,
            x=70,
            y=80,
            w=20,
            h=30,
            text_x=65,
            text_y=112,
        ),
        "Sales Manager": AgentConfig(
            role="Sales Manager",
            label="Sales",
            color=9,
            x=120,
            y=80,
            w=20,
            h=30,
            text_x=120,
            text_y=112,
        ),
        "CPO": AgentConfig(
            role="CPO",
            label="CPO",
            color=12,
            x=140,
            y=40,
            w=20,
            h=30,
            text_x=135,
            text_y=72,
        ),
    }


class SimulationConfig(BaseSettings):
    """Configuration for the Pyxel Simulation UI."""

    # Window
    width: int = 160
    height: int = 120
    fps: int = 30
    title: str = MSG_SIM_TITLE
    bg_color: int = 0
    text_color: int = 7

    # Dialogue
    chars_per_line: int = 38
    line_height: int = 8
    dialogue_x: int = 5
    dialogue_y: int = 15
    max_y: int = 75
    waiting_msg: str = MSG_WAITING_FOR_DEBATE

    # Fallback Console
    console_sleep: float = 0.5
    max_turns: int = 5

    # Agent Map (Role -> Config)
    # Using default_factory to allow overrides and load from external source if needed
    agents: dict[str, AgentConfig] = Field(default_factory=_load_default_agents_config)

    @field_validator("width", "height")
    @classmethod
    def validate_resolution(cls, v: int) -> int:
        if v <= 0:
            raise ValueError(ERR_INVALID_RESOLUTION)
        return v

    @field_validator("fps")
    @classmethod
    def validate_fps(cls, v: int) -> int:
        if not (1 <= v <= 60):
            raise ValueError(ERR_INVALID_FPS)
        return v

    @field_validator("bg_color", "text_color")
    @classmethod
    def validate_color(cls, v: int) -> int:
        if not (0 <= v <= 15):
            raise ValueError(ERR_INVALID_COLOR)
        return v


class Settings(BaseSettings):
    """Configuration settings for the application."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="forbid"
    )

    # API Keys
    openai_api_key: SecretStr | None = Field(alias="OPENAI_API_KEY", default=None)
    tavily_api_key: SecretStr | None = Field(alias="TAVILY_API_KEY", default=None)
    v0_api_key: SecretStr | None = Field(alias="V0_API_KEY", default=None)

    # Model Configuration
    llm_model: str = Field(alias="LLM_MODEL", default="gpt-4o")

    # Search Configuration
    search_max_results: int = Field(alias="SEARCH_MAX_RESULTS", default=5)
    search_depth: str = Field(alias="SEARCH_DEPTH", default="advanced")
    search_query_template: str = Field(
        alias="SEARCH_QUERY_TEMPLATE",
        default="emerging business trends and painful problems in {topic}",
    )

    # Logging
    log_level: str = Field(alias="LOG_LEVEL", default="INFO")

    # UI Page Size (also used in UIConfig but can be overridden by env)
    ui_page_size: int = Field(alias="UI_PAGE_SIZE", default=5)

    validation: ClassVar[ValidationConfig] = ValidationConfig()
    errors: ClassVar[ErrorMessages] = ErrorMessages()
    ui: ClassVar[UIConfig] = UIConfig()
    simulation: ClassVar[SimulationConfig] = SimulationConfig()

    def validate_api_keys(self) -> Self:
        """Validate API keys are present."""
        if not self.openai_api_key:
            raise ValueError(ERR_CONFIG_MISSING_OPENAI_KEY)
        if not self.tavily_api_key:
            raise ValueError(ERR_CONFIG_MISSING_TAVILY_KEY)
        return self

    def rotate_keys(self) -> None:
        """
        Placeholder for key rotation logic.
        In production, this would fetch new keys from a secret manager.
        """


@lru_cache
def get_settings() -> Settings:
    """Load and cache settings."""
    return Settings()
