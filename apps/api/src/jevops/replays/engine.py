"""Replay engine: re-evaluate historical decisions with different policy/thresholds."""

from __future__ import annotations

from typing import Any

from jevops.decisions.service import _judgments_to_namespace, _simple_disposition
from jevops.jev.types import JudgmentResult, QuestionType
from jevops.policies.engine import PolicyEngine
from jevops.policies.schema import PolicyConfig


class ReplayResult:
    def __init__(
        self,
        original_disposition: str,
        new_disposition: str,
        namespace: dict[str, Any],
        trace: dict[str, Any] | None = None,
    ) -> None:
        self.original_disposition = original_disposition
        self.new_disposition = new_disposition
        self.changed = original_disposition != new_disposition
        self.namespace = namespace
        self.trace = trace


def replay_decision(
    decision_data: dict[str, Any],
    judgments_data: list[dict[str, Any]],
    policy_config: PolicyConfig | None = None,
) -> ReplayResult:
    """Re-evaluate a single decision using stored judgments and a (possibly different) policy."""
    # Reconstruct judgment results
    judgment_results = []
    for j in judgments_data:
        value = j.get("value", {})
        judgment_results.append(
            JudgmentResult(
                question_key=j["question_key"],
                question_type=QuestionType(j["question_type"]),
                value=value.get("value") if isinstance(value, dict) else value,
                probabilities=value.get("probabilities") if isinstance(value, dict) else None,
                confidence=j.get("confidence"),
            )
        )

    namespace = _judgments_to_namespace(judgment_results)
    original = decision_data.get("disposition", "")

    if policy_config:
        engine = PolicyEngine()
        result = engine.evaluate(policy_config, namespace)
        new_disposition = result.disposition
        trace = result.to_dict()
    else:
        new_disposition = _simple_disposition(namespace).value
        trace = {"engine": "simple", "namespace": namespace}

    return ReplayResult(
        original_disposition=original,
        new_disposition=new_disposition,
        namespace=namespace,
        trace=trace,
    )
