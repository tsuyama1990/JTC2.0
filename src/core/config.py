from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for the application."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # API Keys
    openai_api_key: SecretStr | None = Field(default=None, alias="OPENAI_API_KEY")
    tavily_api_key: SecretStr | None = Field(default=None, alias="TAVILY_API_KEY")

    # Model Configuration
    llm_model: str = Field(default="gpt-4o", description="The LLM model to use")

    # Search Configuration
    search_max_results: int = Field(default=5, description="Maximum number of search results")
    search_depth: str = Field(default="advanced", description="Search depth (basic or advanced)")
    search_query_template: str = Field(
        default="emerging business trends and painful problems in {topic}",
        description="Template for search queries",
    )

    # UI Configuration
    ui_page_size: int = Field(default=5, description="Number of ideas to display per page")

    # Validation for critical keys
    def validate_keys(self) -> None:
        """Validate that critical keys are present."""
        if not self.openai_api_key:
            # We don't crash here to allow for testing or partial usage,
            # but specific components will raise errors if they need it.
            pass


# Global settings instance
settings = Settings()
