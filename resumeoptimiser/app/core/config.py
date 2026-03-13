"""Application configuration using pydantic-settings.

All settings are loaded from environment variables / .env file.
No global state – instantiated once and injected via dependency injection.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path to the .env file so it is found regardless of the working
# directory from which uvicorn is launched.
_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


@dataclass
class LLMProviderConfig:
    """Concrete provider configuration for an OpenAI-compatible endpoint."""

    name: str
    base_url: str
    model: str
    api_key: str
    temperature: float
    top_p: float
    max_tokens: int
    timeout: float


class LLMSettings(BaseSettings):
    """Settings scoped to LLM providers (supports multiple for rotation)."""

    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Legacy/default provider (kept for backward compatibility)
    provider: str = Field(default="nvidia")
    base_url: str = Field(default="https://integrate.api.nvidia.com/v1")
    model: str = Field(default="openai/gpt-oss-120b")
    api_key: str = Field(default="")

    # Shared tuning knobs
    temperature: float = Field(default=1.0, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    max_tokens: int = Field(default=4096, gt=0)
    # Total wall-clock timeout (seconds) for a single LLM API call.
    # Covers connect + read. 0 = no timeout (not recommended).
    timeout: float = Field(default=300.0, ge=0.0)

    # OpenRouter (free tier) – preferred primary when available
    openrouter_api_key: str = Field(default="")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1")
    openrouter_model: str = Field(default="openrouter/free")

    # NVIDIA NIM – retained so we can rotate/fallback when keys work again
    nvidia_api_key: str = Field(default="")
    nvidia_base_url: str = Field(default="https://integrate.api.nvidia.com/v1")
    nvidia_model: str = Field(default="openai/gpt-oss-120b")

    def provider_configs(self) -> list[LLMProviderConfig]:
        """Return enabled providers ordered for rotation/failover."""

        providers: list[LLMProviderConfig] = []

        if self.openrouter_api_key:
            providers.append(
                LLMProviderConfig(
                    name="openrouter",
                    base_url=self.openrouter_base_url,
                    model=self.openrouter_model,
                    api_key=self.openrouter_api_key,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    max_tokens=self.max_tokens,
                    timeout=self.timeout,
                )
            )

        # Prefer explicit NVIDIA key if provided; otherwise fall back to legacy fields
        if self.nvidia_api_key or (self.provider.lower() == "nvidia" and self.api_key):
            providers.append(
                LLMProviderConfig(
                    name="nvidia",
                    base_url=self.nvidia_base_url or self.base_url,
                    model=self.nvidia_model or self.model,
                    api_key=self.nvidia_api_key or self.api_key,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    max_tokens=self.max_tokens,
                    timeout=self.timeout,
                )
            )

        # Backward-compatible single-provider fallback (any other provider)
        if not providers and self.api_key:
            providers.append(
                LLMProviderConfig(
                    name=self.provider or "default",
                    base_url=self.base_url,
                    model=self.model,
                    api_key=self.api_key,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    max_tokens=self.max_tokens,
                    timeout=self.timeout,
                )
            )

        return providers


class EmbeddingSettings(BaseSettings):
    """Settings scoped to the embedding model."""

    model_config = SettingsConfigDict(
        env_prefix="EMBEDDING_",
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    model: str = Field(default="BAAI/bge-base-en-v1.5")
    device: str = Field(default="cpu")


class DatabaseSettings(BaseSettings):
    """Settings scoped to the database."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(default="postgresql://localhost/resumeoptimiser")


class AppSettings(BaseSettings):
    """Top-level application settings."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
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
