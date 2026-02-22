import sys

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for the application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # API Keys (Required - No default, but Optional here to allow instantiation
    # before validation, though BaseSettings typically validates on init.
    # To satisfy mypy 'Missing named argument' when calling Settings(), we can
    # either use default=None or force them to be passed.
    # Since we want them loaded from env, we use Optional + Validation check or default=None.)
    openai_api_key: SecretStr | None = Field(alias="OPENAI_API_KEY", default=None)
    tavily_api_key: SecretStr | None = Field(alias="TAVILY_API_KEY", default=None)

    # Model Configuration
    llm_model: str = Field(alias="LLM_MODEL", default="gpt-4o")

    # Search Configuration
    search_max_results: int = Field(alias="SEARCH_MAX_RESULTS", default=5)
    search_depth: str = Field(alias="SEARCH_DEPTH", default="advanced")
    search_query_template: str = Field(
        alias="SEARCH_QUERY_TEMPLATE",
        default="emerging business trends and painful problems in {topic}"
    )

    # UI Configuration
    ui_page_size: int = Field(alias="UI_PAGE_SIZE", default=5)

    # Logging
    log_level: str = Field(alias="LOG_LEVEL", default="INFO")


def load_settings() -> Settings:
    """Load and validate settings."""
    try:
        s = Settings()
        # Validation Logic:
        # We allow missing keys ONLY if we are in a testing environment (pytest)
        # to prevent import errors during test collection.
        # Tests will patch the settings anyway.
        if "pytest" in sys.modules:
            return s

        # Explicit validation after load for production/runtime
        if not s.openai_api_key:
            msg = "OPENAI_API_KEY is missing"
            raise ValueError(msg)
        if not s.tavily_api_key:
            msg = "TAVILY_API_KEY is missing"
            raise ValueError(msg)
        return s
    except Exception as e:
        # We use print here because logging might not be configured yet
        # and this is a fatal startup error.
        sys.stderr.write(f"Configuration Error: {e}\n")
        sys.stderr.write("Please ensure .env file exists and contains all required keys.\n")
        sys.exit(1)


# Global settings instance
settings = load_settings()
