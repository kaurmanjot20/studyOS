"""Global search route."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.search_service import SearchService

router = APIRouter(tags=["search"])


@router.get("/search")
async def search(q: str = "", db: AsyncSession = Depends(get_db)):
    return await SearchService(db).search(q)
