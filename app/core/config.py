import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "DevMatch API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    DATABASE_URL: str = (
        "postgresql+psycopg://devmatch:devmatch@localhost:5432/devmatch"
    )

    FRONTEND_DIR: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "frontend",
        "dist",
    )

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    CORS_ORIGINS: list[str] = ["*"]

    EMBEDDING_DIMENSION: int = 256
    EMBEDDING_SKILL_WEIGHT: float = 3.0
    EMBEDDING_TECHNOLOGY_WEIGHT: float = 2.0
    EMBEDDING_DOMAIN_WEIGHT: float = 2.0
    EMBEDDING_PROJECT_WEIGHT: float = 1.0
    EMBEDDING_BIO_WEIGHT: float = 1.0

    MATCHING_EMBEDDING_WEIGHT: float = 0.7
    MATCHING_SKILL_WEIGHT: float = 0.2
    MATCHING_EXPERIENCE_WEIGHT: float = 0.1
    MATCHING_DEFAULT_LIMIT: int = 10
    MATCHING_MAX_LIMIT: int = 50

    # -- OAuth (social login) -------------------------------------------
    # Each provider is enabled by setting its client ID + secret.
    # Redirect URIs are FRONTEND pages (the SPA completes the flow via the
    # API), e.g. http://localhost:5173/auth/callback — register exactly
    # this URL in each provider's console.
    FRONTEND_URL: str = "http://localhost:5173"
    OAUTH_STATE_EXPIRE_MINUTES: int = 10

    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str | None = None

    GITHUB_CLIENT_ID: str | None = None
    GITHUB_CLIENT_SECRET: str | None = None
    GITHUB_REDIRECT_URI: str | None = None

    LINKEDIN_CLIENT_ID: str | None = None
    LINKEDIN_CLIENT_SECRET: str | None = None
    LINKEDIN_REDIRECT_URI: str | None = None

    # -- Scale / hardening ----------------------------------------------
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_AUTH_PER_MINUTE: int = 30
    RATE_LIMIT_DEFAULT_PER_MINUTE: int = 120
    RECOMMENDATION_CACHE_TTL_SECONDS: int = 60

    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE_SECONDS: int = 1800
    DB_POOL_TIMEOUT_SECONDS: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
