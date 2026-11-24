
"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MoneyLens UG"
    app_env: str = "development"
    debug: bool = True

    database_url: str
    secret_key: str

    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    anthropic_api_key: str | None = None
    enable_llm: bool = False

    cors_origins: list[str] = [
        "http://localhost:8502",
        "http://127.0.0.1:8502",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()  # type: ignore[call-arg]
