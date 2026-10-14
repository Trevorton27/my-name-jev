from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from jevops.auth.middleware import AuthContext, require_api_key
from jevops.database.repositories.decision_repo import DecisionRepository
from jevops.database.session import get_db
from jevops.decisions.schemas import (
    DecisionResponse,
    EvaluateRequest,
    FeedbackRequest,
    JudgmentResponse,
    OutcomeRequest,
)
from jevops.decisions.service import DecisionService
from jevops.jev.mock_provider import MockProvider
from jevops.models.decision_outcome import DecisionOutcome

logger = structlog.stdlib.get_logger()
router = APIRouter(prefix="/decisions", tags=["decisions"])


class _UnavailableProvider:
    """Stands in for a provider that failed to initialize; every evaluation raises its error."""

    def __init__(self, error: Exception) -> None:
        self.error = error

    async def evaluate(self, state, questions):  # type: ignore[no-untyped-def]
        raise RuntimeError(f"Provider unavailable: {self.error}") from self.error


def _get_provider(request: Request):
    settings = request.app.state.settings
    provider_name = settings.jev.provider

    if provider_name == "typesafe":
        from jevops.jev.typesafe_provider import TypeSafeProvider

        return TypeSafeProvider(
            api_key=settings.jev.api_key,
            model=settings.jev.model,
            timeout=settings.jev.timeout,
        )
    elif provider_name == "failure":
        from jevops.jev.failure_provider import FailureProvider

        return FailureProvider()
    else:
        return MockProvider()


def _to_response(decision) -> DecisionResponse:
    judgments = [
        JudgmentResponse(
            question_key=j.question_key,
            question_type=j.question_type,
            value=j.value.get("value") if isinstance(j.value, dict) else j.value,
            probabilities=j.value.get("probabilities") if isinstance(j.value, dict) else None,
            confidence=j.confidence,
        )
        for j in (decision.judgments or [])
    ]
    return DecisionResponse(
        id=decision.id,
        disposition=decision.disposition,
        final_disposition=decision.final_disposition if decision.final_disposition else None,
        action_type=decision.action_type,
        mode=decision.mode,
        environment=decision.environment,
        judgments=judgments,
        policy_trace=decision.policy_trace,
        provider_latency_ms=decision.provider_latency_ms,
        provider_model=decision.provider_model,
        correlation_id=decision.correlation_id,
        created_at=decision.created_at.isoformat() if decision.created_at else None,
    )


@router.post("/evaluate", response_model=DecisionResponse)
async def evaluate_decision(
    body: EvaluateRequest,
    request: Request,
    auth: AuthContext = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    try:
        provider = _get_provider(request)
    except Exception as exc:
        # A misconfigured provider (e.g. missing/invalid JEVOPS_JEV_API_KEY) must not 500:
        # let the service record a human_review decision with the error in policy_trace.
        logger.error("provider.init_failure", error=str(exc))
        provider = _UnavailableProvider(exc)
    repo = DecisionRepository(db)
    service = DecisionService(repo=repo, provider=provider)

    correlation_id = request.headers.get("X-Correlation-ID")
    decision = await service.evaluate(body, auth, correlation_id=correlation_id)

    # Re-fetch with judgments loaded
    decision = await repo.get_with_judgments(decision.id, auth.org_id)
    return _to_response(decision)


@router.get("", response_model=list[DecisionResponse])
async def list_decisions(
    auth: AuthContext = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    repo = DecisionRepository(db)
    decisions = await repo.list_all(auth.org_id, limit=limit, offset=offset)
    return [_to_response(d) for d in decisions]


@router.get("/{decision_id}", response_model=DecisionResponse)
async def get_decision(
    decision_id: uuid.UUID,
    auth: AuthContext = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    repo = DecisionRepository(db)
    decision = await repo.get_with_judgments(decision_id, auth.org_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")
    return _to_response(decision)


@router.post("/{decision_id}/outcome")
async def record_outcome(
    decision_id: uuid.UUID,
    body: OutcomeRequest,
    auth: AuthContext = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    repo = DecisionRepository(db)
    decision = await repo.get_by_id(decision_id, auth.org_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    outcome = DecisionOutcome(
        org_id=auth.org_id,
        decision_id=decision_id,
        ground_truth_label=body.ground_truth_label,
        outcome_data=body.outcome_data,
    )
    db.add(outcome)
    await db.flush()
    return {"status": "recorded", "outcome_id": str(outcome.id)}


@router.post("/{decision_id}/feedback")
async def record_feedback(
    decision_id: uuid.UUID,
    body: FeedbackRequest,
    auth: AuthContext = Depends(require_api_key),
    db: AsyncSession = Depends(get_db),
):
    repo = DecisionRepository(db)
    decision = await repo.get_by_id(decision_id, auth.org_id)
    if not decision:
        raise HTTPException(status_code=404, detail="Decision not found")

    outcome = DecisionOutcome(
        org_id=auth.org_id,
        decision_id=decision_id,
        feedback=body.feedback,
    )
    db.add(outcome)
    await db.flush()
    return {"status": "recorded"}
