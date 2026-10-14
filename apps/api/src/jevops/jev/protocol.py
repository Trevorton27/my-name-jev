from __future__ import annotations

from typing import Any, Protocol

from jevops.jev.types import ProviderEvaluation, TypedQuestion


class DecisionModelProvider(Protocol):
    async def evaluate(
        self,
        state: dict[str, Any],
        questions: dict[str, TypedQuestion],
    ) -> ProviderEvaluation: ...
