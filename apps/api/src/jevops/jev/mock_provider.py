from __future__ import annotations

import hashlib
import json
import random
import time
from typing import Any

from jevops.jev.types import (
    JudgmentResult,
    ProviderEvaluation,
    QuestionType,
    TypedQuestion,
)


class MockProfile:
    BALANCED = "balanced"
    CAUTIOUS = "cautious"
    PERMISSIVE = "permissive"


PROFILE_BIASES = {
    MockProfile.BALANCED: 0.0,
    MockProfile.CAUTIOUS: -0.2,
    MockProfile.PERMISSIVE: 0.2,
}


class MockProvider:
    def __init__(self, profile: str = MockProfile.BALANCED) -> None:
        self.profile = profile
        self.bias = PROFILE_BIASES.get(profile, 0.0)

    def _seed_from_state(self, state: dict[str, Any]) -> int:
        raw = json.dumps(state, sort_keys=True, default=str)
        return int(hashlib.sha256(raw.encode()).hexdigest()[:8], 16)

    async def evaluate(
        self,
        state: dict[str, Any],
        questions: dict[str, TypedQuestion],
    ) -> ProviderEvaluation:
        start = time.monotonic()
        seed = self._seed_from_state(state)
        rng = random.Random(seed)
        judgments: list[JudgmentResult] = []

        for key, q in questions.items():
            if q.type == QuestionType.NOUL:
                val = max(0.0, min(1.0, rng.random() + self.bias))
                judgments.append(
                    JudgmentResult(
                        question_key=key,
                        question_type=QuestionType.NOUL,
                        value=round(val, 4),
                    )
                )

            elif q.type == QuestionType.CHOICE:
                criteria = q.criteria or {}
                if isinstance(criteria, dict):
                    options = list(criteria.keys())
                else:
                    options = list(criteria)
                if not options:
                    options = ["option_a", "option_b"]
                probs = [rng.random() for _ in options]
                total = sum(probs)
                probs = [round(p / total, 4) for p in probs]
                chosen_idx = probs.index(max(probs))
                judgments.append(
                    JudgmentResult(
                        question_key=key,
                        question_type=QuestionType.CHOICE,
                        value=options[chosen_idx],
                        probabilities=dict(zip(options, probs)),
                        confidence=round(max(probs), 4),
                    )
                )

            elif q.type == QuestionType.SCORE:
                val = round(rng.uniform(1, 10) + self.bias, 2)
                val = max(1.0, min(10.0, val))
                judgments.append(
                    JudgmentResult(
                        question_key=key,
                        question_type=QuestionType.SCORE,
                        value=val,
                        confidence=round(rng.uniform(0.5, 1.0), 4),
                    )
                )

        elapsed = (time.monotonic() - start) * 1000
        return ProviderEvaluation(
            judgments=judgments,
            model="mock",
            latency_ms=round(elapsed, 2),
        )
