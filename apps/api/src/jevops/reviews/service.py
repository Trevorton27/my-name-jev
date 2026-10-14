from __future__ import annotations

import uuid

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from jevops.models.audit_event import AuditEvent
from jevops.models.decision import Decision, Disposition
from jevops.models.review import Review, ReviewStatus

logger = structlog.stdlib.get_logger()


class ReviewService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_review_for_decision(self, decision: Decision) -> Review:
        review = Review(
            org_id=decision.org_id,
            decision_id=decision.id,
            status=ReviewStatus.PENDING.value,
        )
        self.session.add(review)
        await self.session.flush()
        logger.info("review.created", review_id=str(review.id), decision_id=str(decision.id))
        return review

    async def list_reviews(
        self, org_id: uuid.UUID, status: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[Review]:
        query = select(Review).where(Review.org_id == org_id)
        if status:
            query = query.where(Review.status == status)
        query = query.order_by(Review.created_at.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_review(self, review_id: uuid.UUID, org_id: uuid.UUID) -> Review | None:
        result = await self.session.execute(select(Review).where(Review.id == review_id, Review.org_id == org_id))
        return result.scalar_one_or_none()

    async def approve(
        self,
        review_id: uuid.UUID,
        org_id: uuid.UUID,
        reviewer: str,
        reason: str | None = None,
        notes: str | None = None,
    ) -> Review | None:
        review = await self.get_review(review_id, org_id)
        if not review:
            return None

        review.status = ReviewStatus.APPROVED.value
        review.reviewer = reviewer
        review.reason = reason
        review.notes = notes

        # Update decision final disposition
        decision = await self.session.get(Decision, review.decision_id)
        if decision:
            decision.final_disposition = Disposition.ALLOW.value

        await self._audit(org_id, "review.approved", review_id, reviewer)
        await self.session.flush()
        return review

    async def reject(
        self,
        review_id: uuid.UUID,
        org_id: uuid.UUID,
        reviewer: str,
        reason: str,
        notes: str | None = None,
    ) -> Review | None:
        review = await self.get_review(review_id, org_id)
        if not review:
            return None

        review.status = ReviewStatus.REJECTED.value
        review.reviewer = reviewer
        review.reason = reason
        review.notes = notes

        decision = await self.session.get(Decision, review.decision_id)
        if decision:
            decision.final_disposition = Disposition.BLOCK.value

        await self._audit(org_id, "review.rejected", review_id, reviewer)
        await self.session.flush()
        return review

    async def request_retry(
        self,
        review_id: uuid.UUID,
        org_id: uuid.UUID,
        reviewer: str,
        reason: str,
        notes: str | None = None,
    ) -> Review | None:
        review = await self.get_review(review_id, org_id)
        if not review:
            return None

        review.status = ReviewStatus.RETRY_REQUESTED.value
        review.reviewer = reviewer
        review.reason = reason
        review.notes = notes

        decision = await self.session.get(Decision, review.decision_id)
        if decision:
            decision.final_disposition = Disposition.RETRY.value

        await self._audit(org_id, "review.retry_requested", review_id, reviewer)
        await self.session.flush()
        return review

    async def correct_judgments(
        self,
        review_id: uuid.UUID,
        org_id: uuid.UUID,
        reviewer: str,
        corrected: dict,
        notes: str | None = None,
    ) -> Review | None:
        review = await self.get_review(review_id, org_id)
        if not review:
            return None

        review.corrected_judgments = corrected
        review.reviewer = reviewer
        review.notes = notes

        await self._audit(org_id, "review.judgments_corrected", review_id, reviewer)
        await self.session.flush()
        return review

    async def _audit(self, org_id: uuid.UUID, event_type: str, resource_id: uuid.UUID, actor: str) -> None:
        event = AuditEvent(
            org_id=org_id,
            event_type=event_type,
            actor=actor,
            resource_type="review",
            resource_id=str(resource_id),
        )
        self.session.add(event)
