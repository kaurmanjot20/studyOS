"""Application configuration.

Settings are loaded from the environment (and a local `.env` in development) and
validated with pydantic-settings. Nothing in the app reads `os.environ` directly;
everything goes through the `settings` singleton so configuration has a single source
of truth and a single place to validate.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

ProviderName = Literal["openai", "anthropic", "gemini", "openrouter", "ollama"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Core ---
    app_env: Literal["development", "production", "test"] = "development"
    app_secret: str = "change-me"
    encryption_key: str = "change-me"

    # --- Database parts (compose the URLs from these) ---
    postgres_user: str = "interviewos"
    postgres_password: str = "interviewos"
    postgres_db: str = "interviewos"
    postgres_host: str = "db"
    postgres_port: int = 5432
    # Optional explicit override; if unset we build it from the parts above.
    database_url: str | None = None

    # --- Default provider (users configure their own in Settings) ---
    default_llm_provider: ProviderName = "openai"
    default_llm_model: str = "gpt-4o-mini"
    default_embedding_model: str = "text-embedding-3-small"
    # pgvector columns need a fixed dimension. This is the indexed vector size; the
    # embed model + actual dim are also recorded per document, and changing this
    # requires re-embedding. 1536 = OpenAI text-embedding-3-small.
    embedding_dim: int = 1536

    # --- Document pipeline ---
    storage_dir: str = "storage"
    max_upload_mb: int = 25
    chunk_size_chars: int = 1200
    chunk_overlap_chars: int = 180
    embed_batch_size: int = 64
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    openrouter_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"

    # --- CORS ---
    cors_origins: str = "http://localhost:3000"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def async_database_url(self) -> str:
        """SQLAlchemy async (asyncpg) URL used by the running application."""
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sync_database_url(self) -> str:
        """Sync URL used by Alembic and the startup DB-wait check."""
        return self.async_database_url.replace("+asyncpg", "")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
