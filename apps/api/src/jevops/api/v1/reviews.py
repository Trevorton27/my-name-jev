from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from jevops.auth.middleware import AuthContext, require_api_key
from jevops.database.session import get_db
from jevops.reviews.schemas import (
    ApproveRequest,
    CorrectJudgmentsRequest,
    RejectRequest,
    RetryRequest,
    ReviewResponse,
)
from jevops.reviews.service import ReviewService

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _to_response(review) -> ReviewResponse:
    return ReviewResponse(
        id=review.id,
        decision_id=review.decision_id,
        status=review.status.value if hasattr(review.status, "value") else review.status,
        reviewer=review.reviewer,
        reason=review.reason,
        corrected_judgments=review.corrected_judgments,
        notes=review.notes,
        created_at=review.created_at.isoformat() if review.created_at else None,
    )


@router.get("", response_model=list[ReviewResponse])
async def list_reviews(
    status: str | None = None,
    auth: AuthContext = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    service = ReviewService(db)
    reviews = await service.list_reviews(auth.org_id, status=status, limit=limit, offset=offset)
    return [_to_response(r) for r in reviews]


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: uuid.UUID,
    auth: AuthContext = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    service = ReviewService(db)
    review = await service.get_review(review_id, auth.org_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return _to_response(review)


@router.post("/{review_id}/approve", response_model=ReviewResponse)
async def approve_review(
    review_id: uuid.UUID,
    body: ApproveRequest,
    auth: AuthContext = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    service = ReviewService(db)
    review = await service.approve(review_id, auth.org_id, body.reviewer, body.reason, body.notes)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return _to_response(review)


@router.post("/{review_id}/reject", response_model=ReviewResponse)
async def reject_review(
    review_id: uuid.UUID,
    body: RejectRequest,
    auth: AuthContext = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    service = ReviewService(db)
    review = await service.reject(review_id, auth.org_id, body.reviewer, body.reason, body.notes)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return _to_response(review)


@router.post("/{review_id}/request-retry", response_model=ReviewResponse)
async def request_retry(
    review_id: uuid.UUID,
    body: RetryRequest,
    auth: AuthContext = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    service = ReviewService(db)
    review = await service.request_retry(review_id, auth.org_id, body.reviewer, body.reason, body.notes)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return _to_response(review)


@router.post("/{review_id}/correct-judgments", response_model=ReviewResponse)
async def correct_judgments(
    review_id: uuid.UUID,
    body: CorrectJudgmentsRequest,
    auth: AuthContext = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    service = ReviewService(db)
    review = await service.correct_judgments(
        review_id, auth.org_id, body.reviewer, body.corrected_judgments, body.notes
    )
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return _to_response(review)
