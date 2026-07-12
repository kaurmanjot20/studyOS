"""Provider settings business logic.

Owns three things:
  1. Persisting provider settings (with the API key encrypted at rest).
  2. Resolving the *active* provider config, layering saved DB values over `.env`
     fallbacks so development works with zero configuration and production uses the
     user's own keys.
  3. Testing a connection / listing models for a provider (saved or not-yet-saved).
"""

from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decrypt, encrypt
from app.models.provider_settings import ProviderSettings
from app.models.schemas import ConnectionTestRequest, ProviderSettingsUpsert
from app.providers.base import (
    ConnectionStatus,
    LLMProvider,
    ProviderConfig,
    ProviderError,
)
from app.providers.factory import PROVIDER_META, build_provider
from app.providers.fallback import FallbackProvider


def _env_api_key(provider: str) -> str | None:
    return getattr(settings, f"{provider}_api_key", "") or None


def _env_base_url(provider: str) -> str | None:
    if provider == "ollama":
        return settings.ollama_base_url
    return None


class ProviderService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # --- persistence ---

    async def list_settings(self) -> list[ProviderSettings]:
        result = await self.db.execute(select(ProviderSettings))
        return list(result.scalars().all())

    async def _get(self, provider: str) -> ProviderSettings | None:
        return await self.db.get(ProviderSettings, provider)

    async def upsert(self, data: ProviderSettingsUpsert) -> ProviderSettings:
        if data.provider not in PROVIDER_META:
            raise ProviderError(f"Unknown provider: {data.provider!r}")

        row = await self._get(data.provider)
        if row is None:
            row = ProviderSettings(provider=data.provider)
            self.db.add(row)

        # api_key: None → leave as-is; "" → clear; value → encrypt & store.
        if data.api_key is not None:
            row.api_key_encrypted = encrypt(data.api_key) if data.api_key else None
        if data.chat_model is not None:
            row.chat_model = data.chat_model or None
        if data.embedding_model is not None:
            row.embedding_model = data.embedding_model or None
        if data.base_url is not None:
            row.base_url = data.base_url or None

        if data.set_active:
            # Exactly one active provider.
            await self.db.execute(
                update(ProviderSettings).values(is_active=False)
            )
            row.is_active = True

        await self.db.commit()
        await self.db.refresh(row)
        return row

    # --- resolution ---

    async def resolve_active_config(self) -> ProviderConfig:
        """The config the agent uses: active DB row over `.env` fallbacks."""
        result = await self.db.execute(
            select(ProviderSettings).where(ProviderSettings.is_active.is_(True))
        )
        row = result.scalar_one_or_none()

        if row is not None:
            api_key = (
                decrypt(row.api_key_encrypted)
                if row.api_key_encrypted
                else _env_api_key(row.provider)
            )
            return ProviderConfig(
                provider=row.provider,
                api_key=api_key,
                chat_model=row.chat_model or settings.default_llm_model,
                embedding_model=row.embedding_model or settings.default_embedding_model,
                base_url=row.base_url or _env_base_url(row.provider),
            )

        # No saved active provider — fall back entirely to environment defaults.
        provider = settings.default_llm_provider
        return ProviderConfig(
            provider=provider,
            api_key=_env_api_key(provider),
            chat_model=settings.default_llm_model,
            embedding_model=settings.default_embedding_model,
            base_url=_env_base_url(provider),
        )

    def _fallback_config(self) -> ProviderConfig:
        fp = settings.fallback_provider
        return ProviderConfig(
            provider=fp,
            api_key=_env_api_key(fp),
            chat_model=settings.fallback_model,
            embedding_model=settings.fallback_embedding_model,
            base_url=_env_base_url(fp),
        )

    async def resolve_active_provider(
        self, config: ProviderConfig | None = None
    ) -> LLMProvider:
        """Build the provider the agent uses, wrapping it with a local fallback (on
        rate limits) when enabled and the fallback differs from the active provider."""
        if config is None:
            config = await self.resolve_active_config()
        primary = build_provider(config)
        if (
            settings.enable_local_fallback
            and config.provider != settings.fallback_provider
        ):
            fallback = build_provider(self._fallback_config())
            return FallbackProvider(primary, fallback)
        return primary

    async def _config_for_test(self, req: ConnectionTestRequest) -> ProviderConfig:
        row = await self._get(req.provider)
        saved_key = (
            decrypt(row.api_key_encrypted) if row and row.api_key_encrypted else None
        )
        return ProviderConfig(
            provider=req.provider,
            api_key=req.api_key or saved_key or _env_api_key(req.provider),
            chat_model=req.chat_model or (row.chat_model if row else None) or "",
            embedding_model=(row.embedding_model if row else None),
            base_url=req.base_url or (row.base_url if row else None) or _env_base_url(req.provider),
        )

    # --- diagnostics ---

    async def test_connection(self, req: ConnectionTestRequest) -> ConnectionStatus:
        if req.provider not in PROVIDER_META:
            return ConnectionStatus(ok=False, detail=f"Unknown provider: {req.provider}")
        config = await self._config_for_test(req)
        meta = PROVIDER_META[req.provider]
        if meta.requires_api_key and not config.api_key:
            return ConnectionStatus(
                ok=False, detail=f"{meta.label} requires an API key."
            )
        provider = build_provider(config)
        return await provider.test_connection()

    async def list_models(self, provider_name: str) -> list[str]:
        config = await self._config_for_test(
            ConnectionTestRequest(provider=provider_name)
        )
        provider = build_provider(config)
        models = await provider.list_models()
        return [m.id for m in models]
