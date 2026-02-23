from functools import lru_cache
from typing import ClassVar, Self

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.constants import ERR_CONFIG_MISSING_OPENAI_KEY, ERR_CONFIG_MISSING_TAVILY_KEY


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

    unique_id_violation: str = "Generated ideas must have unique IDs."
    config_missing_openai: str = ERR_CONFIG_MISSING_OPENAI_KEY
    config_missing_tavily: str = ERR_CONFIG_MISSING_TAVILY_KEY
    search_config_missing: str = (
        "Search configuration error: API key is missing. Please check your .env file."
    )
    llm_config_missing: str = (
        "LLM configuration error: API key is missing. Please check your .env file."
    )
    search_failed: str = "Search service unavailable."
    llm_failure: str = "LLM generation failed."

    # Validation Errors
    too_many_metrics: str = "Too many custom metrics. Limit is {limit}"
    invalid_metric_key: str = "Metric key '{key}' contains invalid characters."
    missing_persona: str = "Target persona is required for VERIFICATION phase."
    missing_mvp: str = "MVP definition is required for SOLUTION phase."


class UIConfig(BaseSettings):
    """UI Strings and Configuration."""

    page_size: int = Field(alias="UI_PAGE_SIZE", default=5)

    # Messages
    no_ideas: str = "\nNo ideas generated. Please try again or check logs."
    generated_header: str = "\n=== Generated Ideas ==="  # Simplified header
    press_enter: str = "\nPress Enter to see more..."
    select_prompt: str = "\n[GATE 1] Select an Idea ID (0-9) to proceed: "
    id_not_found: str = "ID {idx} not found. Please try again."
    invalid_input: str = "Please enter a valid number."
    selected: str = "\n✓ Selected Plan: {title}"
    cycle_complete: str = "Cycle 1 Complete. State updated."
    topic_empty: str = "Topic cannot be empty."
    phase_start: str = "\nPhase: {phase}"
    researching: str = "Researching and Ideating for: '{topic}'..."
    wait: str = "(This may take 30-60 seconds due to search and LLM generation)..."
    execution_error: str = "\nError during execution: {e}"


class Settings(BaseSettings):
    """Configuration settings for the application."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # API Keys
    openai_api_key: SecretStr | None = Field(alias="OPENAI_API_KEY", default=None)
    tavily_api_key: SecretStr | None = Field(alias="TAVILY_API_KEY", default=None)

    # Model Configuration
    llm_model: str = Field(alias="LLM_MODEL", default="gpt-4o")

    # Search Configuration
    search_max_results: int = Field(alias="SEARCH_MAX_RESULTS", default=5)
    search_depth: str = Field(alias="SEARCH_DEPTH", default="advanced")
    search_query_template: str = Field(
        alias="SEARCH_QUERY_TEMPLATE",
        default="emerging business trends and painful problems in {topic}",
    )

    # UI Configuration (Keep alias for backward compat if needed, but prefer UIConfig)
    ui_page_size: int = Field(alias="UI_PAGE_SIZE", default=5)

    # Logging
    log_level: str = Field(alias="LOG_LEVEL", default="INFO")

    validation: ClassVar[ValidationConfig] = ValidationConfig()
    errors: ClassVar[ErrorMessages] = ErrorMessages()
    ui: ClassVar[UIConfig] = UIConfig()

    def validate_api_keys(self) -> Self:
        """Validate API keys are present."""
        if not self.openai_api_key:
            raise ValueError(ERR_CONFIG_MISSING_OPENAI_KEY)
        if not self.tavily_api_key:
            raise ValueError(ERR_CONFIG_MISSING_TAVILY_KEY)
        return self


@lru_cache
def get_settings() -> Settings:
    """Load and cache settings."""
    return Settings()
