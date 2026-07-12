"""AI provider settings routes (thin).

Exposes provider metadata, saved settings (never the keys), upsert, connection testing,
and model listing. All logic lives in `ProviderService`.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.provider_settings import ProviderSettings
from app.models.schemas import (
    ConnectionTestRequest,
    ConnectionTestResult,
    ModelListResult,
    ProviderMetaRead,
    ProviderSettingsRead,
    ProviderSettingsUpsert,
)
from app.providers.base import ProviderError
from app.providers.factory import available_providers
from app.services.provider_service import ProviderService

router = APIRouter(tags=["settings"])


def get_service(db: AsyncSession = Depends(get_db)) -> ProviderService:
    return ProviderService(db)


def _to_read(row: ProviderSettings) -> ProviderSettingsRead:
    return ProviderSettingsRead(
        provider=row.provider,
        chat_model=row.chat_model,
        embedding_model=row.embedding_model,
        base_url=row.base_url,
        is_active=row.is_active,
        has_api_key=bool(row.api_key_encrypted),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("/providers", response_model=list[ProviderMetaRead])
async def list_providers():
    return [
        ProviderMetaRead(
            name=m.name,
            label=m.label,
            requires_api_key=m.requires_api_key,
            supports_embeddings=m.supports_embeddings,
            default_base_url=m.default_base_url,
        )
        for m in available_providers()
    ]


@router.get("", response_model=list[ProviderSettingsRead])
async def list_settings(service: ProviderService = Depends(get_service)):
    rows = await service.list_settings()
    return [_to_read(r) for r in rows]


@router.put("", response_model=ProviderSettingsRead)
async def upsert_settings(
    payload: ProviderSettingsUpsert, service: ProviderService = Depends(get_service)
):
    try:
        row = await service.upsert(payload)
    except ProviderError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _to_read(row)


@router.post("/test", response_model=ConnectionTestResult)
async def test_connection(
    payload: ConnectionTestRequest, service: ProviderService = Depends(get_service)
):
    status = await service.test_connection(payload)
    return ConnectionTestResult(
        ok=status.ok, detail=status.detail, models_available=status.models_available
    )


@router.get("/models", response_model=ModelListResult)
async def list_models(
    provider: str, service: ProviderService = Depends(get_service)
):
    try:
        models = await service.list_models(provider)
    except ProviderError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return ModelListResult(models=models)
