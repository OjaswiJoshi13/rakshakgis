"""Application settings and configuration management."""

import json
from functools import lru_cache
from typing import List, Union

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Core application settings parsed from environment variables."""

    PROJECT_NAME: str = "RakshakGIS"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = (
        "AI-powered GIS platform for disaster risk assessment, "
        "Red Zone demarcation, village vulnerability analysis, "
        "and climate-resilient relocation planning."
    )
    API_V1_STR: str = "/api/v1"

    # Runtime & Environment configuration matching .env.example
    APP_ENV: str = "development"
    DATA_MODE: str = "demo"
    BACKEND_PORT: int = 8000

    # Database configuration matching .env.example
    POSTGRES_DB: str = "rakshakgis"
    POSTGRES_USER: str = "rakshak"
    POSTGRES_PASSWORD: str = "rakshak_dev_secret"
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = ""

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def assemble_database_url(cls, v: str, info) -> str:
        """Resolve database URL from DATABASE_URL or component environment variables."""
        if v and "${" not in v:
            return v
        data = info.data
        user = data.get("POSTGRES_USER", "rakshak")
        password = data.get("POSTGRES_PASSWORD", "rakshak_dev_secret")
        host = data.get("POSTGRES_HOST", "db")
        port = data.get("POSTGRES_PORT", 5432)
        db = data.get("POSTGRES_DB", "rakshakgis")
        return f"postgresql://{user}:{password}@{host}:{port}/{db}"

    # CORS configuration for local frontend development (Next.js / Vite)
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Support comma-separated strings or JSON arrays in environment variables."""
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
