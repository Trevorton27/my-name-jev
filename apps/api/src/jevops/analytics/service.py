from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from jevops.models.decision import Decision
from jevops.models.review import Review


class AnalyticsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_overview(self, org_id: uuid.UUID) -> dict[str, Any]:
        from datetime import datetime, timedelta

        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())

        # Total decisions
        total = await self.session.execute(select(func.count(Decision.id)).where(Decision.org_id == org_id))
        total_count = total.scalar() or 0

        # Decisions today
        today_result = await self.session.execute(
            select(func.count(Decision.id)).where(Decision.org_id == org_id, Decision.created_at >= today_start)
        )
        decisions_today = today_result.scalar() or 0

        # Decisions this week
        week_result = await self.session.execute(
            select(func.count(Decision.id)).where(Decision.org_id == org_id, Decision.created_at >= week_start)
        )
        decisions_this_week = week_result.scalar() or 0

        # Disposition breakdown
        disposition_query = await self.session.execute(
            select(Decision.disposition, func.count(Decision.id))
            .where(Decision.org_id == org_id)
            .group_by(Decision.disposition)
        )
        disposition_breakdown = {row[0]: row[1] for row in disposition_query.all()}

        # Latency stats
        latency_query = await self.session.execute(
            select(
                func.avg(Decision.provider_latency_ms),
                func.percentile_cont(0.95).within_group(Decision.provider_latency_ms),
                func.percentile_cont(0.99).within_group(Decision.provider_latency_ms),
            ).where(Decision.org_id == org_id, Decision.provider_latency_ms.is_not(None))
        )
        latency_row = latency_query.one_or_none()

        # Reviews pending
        pending = await self.session.execute(
            select(func.count(Review.id)).where(Review.org_id == org_id, Review.status == "pending")
        )

        return {
            "total_decisions": total_count,
            "decisions_today": decisions_today,
            "decisions_this_week": decisions_this_week,
            "disposition_breakdown": disposition_breakdown,
            "avg_latency_ms": round(float(latency_row[0] or 0), 2) if latency_row else 0,
            "p95_latency_ms": round(float(latency_row[1] or 0), 2) if latency_row else 0,
            "p99_latency_ms": round(float(latency_row[2] or 0), 2) if latency_row else 0,
            "pending_reviews": pending.scalar() or 0,
        }

    async def get_disposition_breakdown(self, org_id: uuid.UUID, days: int = 30) -> dict[str, Any]:
        from datetime import datetime, timedelta

        cutoff = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(Decision.disposition, func.count(Decision.id))
            .where(Decision.org_id == org_id, Decision.created_at >= cutoff)
            .group_by(Decision.disposition)
        )
        return {row[0]: row[1] for row in result.all()}

    async def get_override_stats(self, org_id: uuid.UUID) -> dict[str, Any]:
        result = await self.session.execute(
            select(func.count(Decision.id)).where(
                Decision.org_id == org_id,
                Decision.final_disposition.is_not(None),
                Decision.final_disposition != Decision.disposition,
            )
        )
        total_overrides = result.scalar() or 0

        total = await self.session.execute(
            select(func.count(Decision.id)).where(
                Decision.org_id == org_id,
                Decision.final_disposition.is_not(None),
            )
        )
        total_with_final = total.scalar() or 0

        return {
            "total_overrides": total_overrides,
            "total_with_final": total_with_final,
            "override_rate": total_overrides / max(total_with_final, 1),
        }
