import sys
from typing import ClassVar

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
    missing_persona: str = "Target persona is required for VERIFICATION phase."
    missing_mvp: str = "MVP definition is required for SOLUTION phase."


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

    # UI Configuration
    ui_page_size: int = Field(alias="UI_PAGE_SIZE", default=5)

    # Logging
    log_level: str = Field(alias="LOG_LEVEL", default="INFO")

    validation: ClassVar[ValidationConfig] = ValidationConfig()
    errors: ClassVar[ErrorMessages] = ErrorMessages()


def _validate_settings(s: Settings) -> None:
    if not s.openai_api_key:
        raise ValueError(ERR_CONFIG_MISSING_OPENAI_KEY)
    if not s.tavily_api_key:
        raise ValueError(ERR_CONFIG_MISSING_TAVILY_KEY)


def load_settings() -> Settings:
    """Load and validate settings."""
    try:
        s = Settings()
        if "pytest" not in sys.modules:
            _validate_settings(s)
    except Exception as e:
        sys.stderr.write(f"Configuration Error: {e}\n")
        sys.stderr.write("Please ensure .env file exists and contains all required keys.\n")
        sys.exit(1)
    else:
        return s


# Global settings instance
settings = load_settings()
