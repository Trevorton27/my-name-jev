from __future__ import annotations

from typing import Any

import structlog

from jevops.auth.middleware import AuthContext
from jevops.database.repositories.decision_repo import DecisionRepository
from jevops.decisions.schemas import EvaluateRequest
from jevops.jev.protocol import DecisionModelProvider
from jevops.jev.types import JudgmentResult, ProviderEvaluation, QuestionType, TypedQuestion
from jevops.models.decision import Decision, Disposition, Judgment

logger = structlog.stdlib.get_logger()


def _default_questions(action_type: str) -> dict[str, TypedQuestion]:
    return {
        "action_appropriate": TypedQuestion(
            type=QuestionType.NOUL,
            instructions=f"Is this {action_type} action appropriate given the current state and evidence?",
        ),
        "risk_level": TypedQuestion(
            type=QuestionType.SCORE,
            instructions="Rate the operational risk of this action from 1 (minimal) to 10 (critical).",
            criteria=["potential for harm", "reversibility", "scope of impact"],
        ),
        "recommended_route": TypedQuestion(
            type=QuestionType.CHOICE,
            instructions="What is the recommended disposition for this action?",
            criteria={
                "allow": "Action is safe and appropriate",
                "retry": "Action needs modification before proceeding",
                "human_review": "Action requires human judgment",
                "block": "Action should not proceed",
            },
        ),
    }


def _judgments_to_namespace(judgments: list[JudgmentResult]) -> dict[str, Any]:
    ns: dict[str, Any] = {}
    for j in judgments:
        if j.question_type == QuestionType.NOUL:
            ns[j.question_key] = j.value
        elif j.question_type == QuestionType.CHOICE or j.question_type == QuestionType.SCORE:
            ns[j.question_key] = j.value
            if j.confidence is not None:
                ns[f"{j.question_key}_confidence"] = j.confidence
    return ns


def _simple_disposition(namespace: dict[str, Any]) -> str:
    """Default disposition logic when no policy engine is available."""
    recommended = namespace.get("recommended_route", "")
    if recommended == "block":
        return Disposition.BLOCK.value
    if recommended == "human_review":
        return Disposition.HUMAN_REVIEW.value
    if recommended == "retry":
        return Disposition.RETRY.value

    risk = namespace.get("risk_level", 5.0)
    appropriateness = namespace.get("action_appropriate", 0.5)

    if risk >= 8.0 or appropriateness < 0.2:
        return Disposition.BLOCK.value
    if risk >= 6.0 or appropriateness < 0.4:
        return Disposition.HUMAN_REVIEW.value
    if risk >= 4.0 or appropriateness < 0.6:
        return Disposition.RETRY.value
    return Disposition.ALLOW.value


class DecisionService:
    def __init__(
        self,
        repo: DecisionRepository,
        provider: DecisionModelProvider,
        policy_engine: Any | None = None,
    ) -> None:
        self.repo = repo
        self.provider = provider
        self.policy_engine = policy_engine

    async def evaluate(
        self,
        request: EvaluateRequest,
        auth: AuthContext,
        correlation_id: str | None = None,
    ) -> Decision:
        # Idempotency check
        if request.idempotency_key:
            existing = await self.repo.get_by_idempotency_key(request.idempotency_key, auth.org_id)
            if existing:
                logger.info("decision.idempotent_hit", key=request.idempotency_key)
                return existing

        # Build questions
        if request.questions:
            questions = {
                k: TypedQuestion(type=v.type, instructions=v.instructions, criteria=v.criteria)
                for k, v in request.questions.items()
            }
        else:
            questions = _default_questions(request.action_type)

        # Call provider
        try:
            evaluation: ProviderEvaluation = await self.provider.evaluate(
                state={
                    "action": request.action,
                    "objective": request.objective,
                    "state": request.state,
                    "evidence": request.evidence,
                },
                questions=questions,
            )
        except Exception as exc:
            logger.error("provider.failure", error=str(exc))
            # Never silently ALLOW on failure
            evaluation = ProviderEvaluation(judgments=[], model="failed")
            disposition = Disposition.HUMAN_REVIEW.value
            policy_trace = {"error": str(exc), "fallback": "human_review"}

            decision = Decision(
                org_id=auth.org_id,
                agent_id=request.agent_id,
                action_type=request.action_type,
                action=request.action,
                objective=request.objective,
                state=request.state,
                evidence=request.evidence,
                disposition=disposition,
                policy_trace=policy_trace,
                provider_model="failed",
                environment=request.environment,
                mode="observe",
                correlation_id=correlation_id,
                idempotency_key=request.idempotency_key,
            )
            return await self.repo.create(decision)

        # Build namespace from judgments
        namespace = _judgments_to_namespace(evaluation.judgments)

        # Evaluate disposition
        if self.policy_engine:
            result = self.policy_engine.evaluate(namespace)
            disposition = Disposition(result["disposition"])
            policy_trace = result.get("trace", {})
        else:
            disposition = _simple_disposition(namespace)
            policy_trace = {"engine": "simple", "namespace": namespace}

        # Create decision
        decision = Decision(
            org_id=auth.org_id,
            agent_id=request.agent_id,
            action_type=request.action_type,
            action=request.action,
            objective=request.objective,
            state=request.state,
            evidence=request.evidence,
            disposition=disposition,
            policy_trace=policy_trace,
            provider_latency_ms=evaluation.latency_ms,
            provider_model=evaluation.model,
            environment=request.environment,
            mode="observe",
            correlation_id=correlation_id,
            idempotency_key=request.idempotency_key,
        )
        decision = await self.repo.create(decision)

        # Store judgments
        for j in evaluation.judgments:
            judgment = Judgment(
                decision_id=decision.id,
                question_key=j.question_key,
                question_type=j.question_type.value,
                value={"value": j.value, "probabilities": j.probabilities},
                confidence=j.confidence,
                raw_response=j.raw,
            )
            await self.repo.add_judgment(judgment)

        return decision
