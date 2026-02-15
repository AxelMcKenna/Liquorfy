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
    default_radius_km: float = 2.0

    # CORS configuration
    cors_origins: str = Field("*", env="CORS_ORIGINS")

    feature_enabled_chains: Dict[str, bool] = Field(default_factory=dict)

    admin_username: str = Field("admin", env="ADMIN_USERNAME")
    admin_password: str = Field("admin", env="ADMIN_PASSWORD")

    class Config:
        env_file = ".env"
        case_sensitive = False

    @validator("secret_key")
    def validate_secret_key(cls, v: str) -> str:
        """Validate SECRET_KEY meets security requirements."""
        # List of insecure default values
        insecure_defaults = [
            "changeme",
            "change-me",
            "dev-secret",
            "secret",
            "password",
            "admin",
        ]

        # Check length
        if len(v) < 32:
            raise ValueError(
                f"SECRET_KEY must be at least 32 characters long (current: {len(v)}). "
                "Generate a secure key with: openssl rand -base64 32"
            )

        # Check for common insecure values
        if v.lower() in insecure_defaults:
            raise ValueError(
                f"SECRET_KEY cannot be a default value. "
                "Generate a secure key with: openssl rand -base64 32"
            )

        return v

    @validator("admin_password")
    def validate_admin_password(cls, v: str) -> str:
        """Warn about weak admin passwords."""
        if v in ["admin", "password", "changeme"]:
            import warnings
            warnings.warn(
                "Using default admin password. Change this in production!",
                UserWarning
            )

        if len(v) < 8:
            import warnings
            warnings.warn(
                f"Admin password is weak (length: {len(v)}). Use at least 12 characters.",
                UserWarning
            )

        return v

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
