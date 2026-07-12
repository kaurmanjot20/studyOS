"""Provider settings model.

One row per configured provider. The API key is stored encrypted (never in plaintext,
never returned to the client). Exactly one row may be `is_active` — that's the provider
the agent uses. In dev, a missing key falls back to the corresponding `.env` value.
"""

from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ProviderSettings(TimestampMixin, Base):
    __tablename__ = "provider_settings"

    # Provider name is the natural key ("openai", "anthropic", ...).
    provider: Mapped[str] = mapped_column(String(32), primary_key=True)
    api_key_encrypted: Mapped[str | None] = mapped_column(String, nullable=True)
    chat_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    embedding_model: Mapped[str | None] = mapped_column(String(120), nullable=True)
    base_url: Mapped[str | None] = mapped_column(String(300), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
