"""Application configuration loaded from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "AEGIS"
    app_version: str = "0.1.0"
    debug: bool = True

    database_url: str = "sqlite:///./aegis.db"
    api_v1_prefix: str = "/api/v1"

    secret_key: str = "change-this-in-production"
    access_token_expire_minutes: int = 60

    llm_provider: str = "mock"
    mock_provider_enabled: bool = True


settings = Settings()