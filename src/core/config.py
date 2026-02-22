from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration settings for the application."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: SecretStr | None = Field(default=None, alias="OPENAI_API_KEY")
    tavily_api_key: SecretStr | None = Field(default=None, alias="TAVILY_API_KEY")

    # Validation for critical keys
    def validate_keys(self) -> None:
        """Validate that critical keys are present."""
        if not self.openai_api_key:
            # We don't crash here to allow for testing or partial usage,
            # but specific components will raise errors if they need it.
            pass


# Global settings instance
settings = Settings()
