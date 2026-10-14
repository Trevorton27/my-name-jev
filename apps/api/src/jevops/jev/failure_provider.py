from __future__ import annotations

import asyncio
import random
from typing import Any

from jevops.jev.types import ProviderEvaluation, TypedQuestion


class ProviderTimeoutError(Exception):
    pass


class ProviderRateLimitError(Exception):
    pass


class ProviderMalformedResponseError(Exception):
    pass


class FailureProvider:
    """Simulates provider failures for testing resilience."""

    def __init__(
        self,
        timeout_rate: float = 0.3,
        rate_limit_rate: float = 0.2,
        malformed_rate: float = 0.1,
    ) -> None:
        self.timeout_rate = timeout_rate
        self.rate_limit_rate = rate_limit_rate
        self.malformed_rate = malformed_rate

    async def evaluate(
        self,
        state: dict[str, Any],
        questions: dict[str, TypedQuestion],
    ) -> ProviderEvaluation:
        roll = random.random()

        if roll < self.timeout_rate:
            await asyncio.sleep(0.01)
            raise ProviderTimeoutError("Simulated provider timeout")

        if roll < self.timeout_rate + self.rate_limit_rate:
            raise ProviderRateLimitError("Simulated rate limit (429)")

        if roll < self.timeout_rate + self.rate_limit_rate + self.malformed_rate:
            raise ProviderMalformedResponseError("Simulated malformed response")

        # Remaining calls succeed with empty evaluation
        return ProviderEvaluation(
            judgments=[],
            model="failure-sim",
            latency_ms=0.0,
        )
