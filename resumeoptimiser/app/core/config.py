"""Application configuration using pydantic-settings.

All settings are loaded from environment variables / .env file.
No global state – instantiated once and injected via dependency injection.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    """Settings scoped to the LLM provider."""

    model_config = SettingsConfigDict(env_prefix="LLM_", extra="ignore")

    provider: str = Field(default="nvidia")
    base_url: str = Field(default="https://integrate.api.nvidia.com/v1")
    model: str = Field(default="deepseek-ai/deepseek-r1-distill-qwen-32b")
    api_key: str = Field(default="")
    temperature: float = Field(default=0.6, ge=0.0, le=2.0)
    top_p: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=4096, gt=0)


class EmbeddingSettings(BaseSettings):
    """Settings scoped to the embedding model."""

    model_config = SettingsConfigDict(env_prefix="EMBEDDING_", extra="ignore")

    model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    device: str = Field(default="cpu")


class DatabaseSettings(BaseSettings):
    """Settings scoped to the database."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    database_url: str = Field(default="postgresql://localhost/resumeoptimiser")


class AppSettings(BaseSettings):
    """Top-level application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development")
    app_debug: bool = Field(default=False)
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")

    llm: LLMSettings = Field(default_factory=LLMSettings)
    embedding: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """Return the singleton settings instance (cached after first call)."""
    return AppSettings()
