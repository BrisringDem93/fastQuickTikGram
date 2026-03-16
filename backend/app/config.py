from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ------------------------------------------------------------------
    # Database & cache
    # ------------------------------------------------------------------
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost/fastquicktikgram"
    REDIS_URL: str = "redis://localhost:6379/0"

    # ------------------------------------------------------------------
    # Security / JWT
    # ------------------------------------------------------------------
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Fernet key for encrypting OAuth tokens at rest (base64-url 32 bytes)
    ENCRYPTION_KEY: str

    # ------------------------------------------------------------------
    # Local filesystem storage
    # ------------------------------------------------------------------
    # Directory where uploaded and processed videos are stored inside the container.
    # Mount a persistent Docker volume here so files survive container restarts.
    UPLOAD_DIR: str = "/app/uploads"

    # Public HTTPS root of the backend used to build media download URLs for
    # social-platform publishing APIs (e.g. "https://api.yourdomain.com").
    # Leave empty during local development; set it in production.
    PUBLIC_BASE_URL: str = ""

    # ------------------------------------------------------------------
    # OpenAI
    # ------------------------------------------------------------------
    OPENAI_API_KEY: str

    # ------------------------------------------------------------------
    # YouTube OAuth2
    # ------------------------------------------------------------------
    YOUTUBE_CLIENT_ID: str = ""
    YOUTUBE_CLIENT_SECRET: str = ""
    YOUTUBE_REDIRECT_URI: str = ""

    # ------------------------------------------------------------------
    # TikTok OAuth
    # ------------------------------------------------------------------
    TIKTOK_CLIENT_KEY: str = ""
    TIKTOK_CLIENT_SECRET: str = ""
    TIKTOK_REDIRECT_URI: str = ""

    # ------------------------------------------------------------------
    # Instagram (Facebook Graph API)
    # ------------------------------------------------------------------
    INSTAGRAM_CLIENT_ID: str = ""
    INSTAGRAM_CLIENT_SECRET: str = ""
    INSTAGRAM_REDIRECT_URI: str = ""

    # ------------------------------------------------------------------
    # Facebook
    # ------------------------------------------------------------------
    FACEBOOK_APP_ID: str = ""
    FACEBOOK_APP_SECRET: str = ""
    FACEBOOK_REDIRECT_URI: str = ""

    # ------------------------------------------------------------------
    # Application limits
    # ------------------------------------------------------------------
    MAX_VIDEO_SIZE_MB: int = 500

    # ------------------------------------------------------------------
    # Celery
    # ------------------------------------------------------------------
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith(("postgresql", "sqlite")):
            raise ValueError("DATABASE_URL must be a PostgreSQL (or SQLite for testing) URL")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings singleton."""
    return Settings()  # type: ignore[call-arg]


settings: Settings = get_settings()
