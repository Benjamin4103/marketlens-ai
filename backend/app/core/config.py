"""
Centralized application configuration.

All environment-dependent values live here. Nothing else in the codebase
should call os.environ directly — import `settings` instead.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "MarketLens AI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret"
    API_V1_PREFIX: str = "/api"

    # Demo mode — if true, or if required API keys are missing, the research
    # pipeline uses deterministic sample data instead of live external calls.
    DEMO_MODE: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/marketlens"
    DATABASE_URL_SYNC: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/marketlens"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # LLM
    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Research APIs
    SEARCH_API_PROVIDER: str = "tavily"
    SEARCH_API_KEY: str = ""
    NEWS_API_KEY: str = ""

    # Auth
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    JWT_ALGORITHM: str = "HS256"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def effective_demo_mode(self) -> bool:
        """Force demo mode on if no LLM key is configured, regardless of flag."""
        if self.DEMO_MODE:
            return True
        if self.LLM_PROVIDER == "openai" and not self.OPENAI_API_KEY:
            return True
        if self.LLM_PROVIDER == "gemini" and not self.GEMINI_API_KEY:
            return True
        return False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
