from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from jevops.analytics.service import AnalyticsService
from jevops.auth.middleware import AuthContext, require_api_key
from jevops.database.session import get_db

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
async def analytics_overview(
    auth: AuthContext = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_overview(auth.org_id)


@router.get("/dispositions")
async def disposition_breakdown(
    days: int = 30,
    auth: AuthContext = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_disposition_breakdown(auth.org_id, days=days)


@router.get("/overrides")
async def override_stats(
    auth: AuthContext = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_override_stats(auth.org_id)
