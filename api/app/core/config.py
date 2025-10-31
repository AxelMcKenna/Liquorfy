from __future__ import annotations

import functools
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

from pydantic import AnyUrl, BaseSettings, Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "Liquorfy API"
    environment: str = Field("development", env="ENVIRONMENT")
    secret_key: str = Field("changeme", env="SECRET_KEY")

    database_url: AnyUrl = Field(
        "postgresql+psycopg://postgres:postgres@db:5432/liquorfy",
        env="DATABASE_URL",
    )
    redis_url: AnyUrl = Field("redis://redis:6379/0", env="REDIS_URL")

    api_cache_ttl_seconds: int = 600
    default_radius_km: float = 20.0

    feature_enabled_chains: Dict[str, bool] = Field(default_factory=dict)

    admin_username: str = Field("admin", env="ADMIN_USERNAME")
    admin_password: str = Field("admin", env="ADMIN_PASSWORD")

    class Config:
        env_file = ".env"
        case_sensitive = False

    @validator("feature_enabled_chains", pre=True)
    def _parse_feature_flags(cls, value: Any) -> Dict[str, bool]:
        if not value:
            return {}
        if isinstance(value, dict):
            return {str(k): bool(v) for k, v in value.items()}
        if isinstance(value, str):
            items: Iterable[str] = value.split(",")
            result: Dict[str, bool] = {}
            for item in items:
                if not item:
                    continue
                key, _, raw = item.partition(":")
                result[key.strip()] = raw.strip().lower() in {"1", "true", "yes"}
            return result
        raise ValueError("Unsupported feature flag format")


@functools.lru_cache()
def get_settings() -> Settings:
    return Settings()


__all__ = ["Settings", "get_settings"]
