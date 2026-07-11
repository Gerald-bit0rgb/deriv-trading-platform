"""
Application configuration.

All settings are loaded from environment variables (or a .env file in dev).
Never hardcode secrets — use environment variables.
"""
from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "Deriv AI Trading Platform"
    APP_ENV: str = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # ── Security ─────────────────────────────────────────────────────────────
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str          # asyncpg driver for async operations
    SYNC_DATABASE_URL: str     # psycopg2 driver for Alembic migrations

    # ── Deriv API ────────────────────────────────────────────────────────────
    DERIV_APP_ID: int = 1
    DERIV_WS_URL: str = "wss://ws.derivws.com/websockets/v3"

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost"

    @property
    def cors_origins_list(self) -> List[str]:
        """Split comma-separated origins into a list."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # ── Firebase ─────────────────────────────────────────────────────────────
    FIREBASE_CREDENTIALS_BASE64: str = ""

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()


# Convenience shortcut used throughout the app
settings = get_settings()
