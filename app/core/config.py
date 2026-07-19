from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Lead Qualification Bot"
    environment: str = "development"
    demo_mode: bool = True
    database_url: str = "sqlite:///./lead_qualification.db"
    openai_api_key: str | None = Field(default=None, repr=False)
    openai_model: str = "gpt-5.6-luna"
    request_timeout_seconds: float = 15.0
    max_retries: int = Field(default=2, ge=0, le=5)
    airtable_api_token: str | None = Field(default=None, repr=False)
    airtable_base_id: str | None = None
    airtable_table_name: str | None = None
    slack_webhook_url: str | None = Field(default=None, repr=False)
    slack_min_priority: Literal["low", "medium", "high"] = "medium"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def airtable_enabled(self) -> bool:
        return all((self.airtable_api_token, self.airtable_base_id, self.airtable_table_name))

    @model_validator(mode="after")
    def validate_live_mode(self) -> "Settings":
        if not self.demo_mode and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when DEMO_MODE=false")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
