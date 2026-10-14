from __future__ import annotations

import time
from typing import Any

import structlog

from jevops.jev.types import (
    JudgmentResult,
    ProviderEvaluation,
    QuestionType,
    TypedQuestion,
)

logger = structlog.stdlib.get_logger()


class TypeSafeProvider:
    def __init__(self, api_key: str, model: str = "jev-latest", timeout: float = 30.0) -> None:
        from typesafe_sdk import AsyncTypeSafeClient, RetryPolicy

        self.model = model
        self.client = AsyncTypeSafeClient(
            api_key=api_key,
            retry=RetryPolicy(max_retries=3, timeout=timeout),
        )

    def _build_questions(self, questions: dict[str, TypedQuestion]) -> dict[str, Any]:
        from typesafe_sdk import Choice, Noul, Score

        sdk_questions: dict[str, Any] = {}
        for key, q in questions.items():
            if q.type == QuestionType.NOUL:
                sdk_questions[key] = Noul(instructions=q.instructions)
            elif q.type == QuestionType.CHOICE:
                criteria = q.criteria if isinstance(q.criteria, dict) else {}
                sdk_questions[key] = Choice(instructions=q.instructions, criteria=criteria)
            elif q.type == QuestionType.SCORE:
                criteria = q.criteria if isinstance(q.criteria, list) else []
                sdk_questions[key] = Score(instructions=q.instructions, criteria=criteria)
        return sdk_questions

    def _extract_judgments(self, response: Any, questions: dict[str, TypedQuestion]) -> list[JudgmentResult]:
        results: list[JudgmentResult] = []
        for key, q in questions.items():
            if q.type == QuestionType.NOUL:
                answer = response.nouls[key]
                results.append(
                    JudgmentResult(
                        question_key=key,
                        question_type=QuestionType.NOUL,
                        value=answer.noul,
                        raw={"noul": answer.noul},
                    )
                )
            elif q.type == QuestionType.CHOICE:
                answer = response.choices[key]
                results.append(
                    JudgmentResult(
                        question_key=key,
                        question_type=QuestionType.CHOICE,
                        value=answer.choice,
                        probabilities=answer.probabilities,
                        confidence=answer.confidence,
                        raw={"choice": answer.choice, "probabilities": answer.probabilities},
                    )
                )
            elif q.type == QuestionType.SCORE:
                answer = response.scores[key]
                results.append(
                    JudgmentResult(
                        question_key=key,
                        question_type=QuestionType.SCORE,
                        value=answer.score,
                        confidence=answer.confidence,
                        raw={"score": answer.score, "probabilities": answer.probabilities},
                    )
                )
        return results

    async def evaluate(
        self,
        state: dict[str, Any],
        questions: dict[str, TypedQuestion],
    ) -> ProviderEvaluation:
        from typesafe_sdk import TypeSafeAPIError

        sdk_questions = self._build_questions(questions)
        start = time.monotonic()

        try:
            response = await self.client.system_one(
                state=state,
                questions=sdk_questions,
            )
        except TypeSafeAPIError as exc:
            logger.error("typesafe.api_error", status=exc.status, request_id=exc.request_id)
            raise

        elapsed = (time.monotonic() - start) * 1000
        judgments = self._extract_judgments(response, questions)

        return ProviderEvaluation(
            judgments=judgments,
            model=self.model,
            latency_ms=round(elapsed, 2),
        )
