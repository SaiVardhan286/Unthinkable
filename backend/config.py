from __future__ import annotations

import logging
from functools import lru_cache
from typing import List

from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings

# Load environment variables from a .env file when present (useful locally).
load_dotenv()


class Settings(BaseSettings):
    # Core environment
    env: str = "dev"

    # Database
    database_url: str = "sqlite:///./unthinkable.db"
    # Minimum times an item must be purchased before being considered in
    # history-based suggestions.
    history_min_purchases: int = 2
    # Number of history-based suggestions to surface.
    history_suggestion_limit: int = 3

    # CORS
    cors_allow_origins: List[str] = ["*"]

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = ""
        case_sensitive = False

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _split_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()  # type: ignore[call-arg]
    logging.getLogger("config").info(
        "Loaded settings",
        extra={"env": settings.env, "database_url": settings.database_url, "log_level": settings.log_level},
    )
    return settings

