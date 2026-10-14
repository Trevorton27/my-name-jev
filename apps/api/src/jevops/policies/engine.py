from __future__ import annotations

from typing import Any

import structlog

from jevops.policies.expression import ExpressionEvalError, UnsafeExpressionError, evaluate_expression
from jevops.policies.schema import PolicyConfig, RuleCondition

logger = structlog.stdlib.get_logger()


class RuleTrace:
    def __init__(self, rule_name: str, priority: int) -> None:
        self.rule_name = rule_name
        self.priority = priority
        self.matched: bool = False
        self.skipped: bool = False
        self.error: str | None = None
        self.reason: str = ""
        self.expressions_evaluated: list[dict[str, Any]] = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule": self.rule_name,
            "priority": self.priority,
            "matched": self.matched,
            "skipped": self.skipped,
            "error": self.error,
            "reason": self.reason,
            "expressions": self.expressions_evaluated,
        }


class PolicyResult:
    def __init__(
        self,
        disposition: str,
        matched_rule: str | None,
        traces: list[RuleTrace],
        namespace: dict[str, Any],
    ) -> None:
        self.disposition = disposition
        self.matched_rule = matched_rule
        self.traces = traces
        self.namespace = namespace

    def to_dict(self) -> dict[str, Any]:
        return {
            "disposition": self.disposition,
            "matched_rule": self.matched_rule,
            "trace": [t.to_dict() for t in self.traces],
            "namespace": self.namespace,
        }


class PolicyEngine:
    def evaluate(self, config: PolicyConfig, namespace: dict[str, Any]) -> PolicyResult:
        # Sort rules by priority (lower = higher priority)
        sorted_rules = sorted(config.rules, key=lambda r: r.priority)
        traces: list[RuleTrace] = []

        for rule in sorted_rules:
            trace = RuleTrace(rule.name, rule.priority)

            try:
                matched = self._evaluate_condition(rule.when, namespace, trace)
            except (UnsafeExpressionError, ExpressionEvalError) as e:
                trace.error = str(e)
                trace.skipped = True
                traces.append(trace)
                logger.warning("policy.rule_error", rule=rule.name, error=str(e))
                continue

            if matched:
                trace.matched = True
                trace.reason = rule.reason
                traces.append(trace)
                return PolicyResult(
                    disposition=rule.then,
                    matched_rule=rule.name,
                    traces=traces,
                    namespace=namespace,
                )
            else:
                trace.skipped = True
                traces.append(trace)

        # No rule matched — use default
        return PolicyResult(
            disposition=config.default,
            matched_rule=None,
            traces=traces,
            namespace=namespace,
        )

    def _evaluate_condition(
        self,
        when: str | RuleCondition,
        namespace: dict[str, Any],
        trace: RuleTrace,
    ) -> bool:
        if isinstance(when, str):
            result = evaluate_expression(when, namespace)
            trace.expressions_evaluated.append({"expr": when, "result": bool(result)})
            return bool(result)

        if isinstance(when, RuleCondition):
            if when.all:
                results = []
                for expr in when.all:
                    val = evaluate_expression(expr, namespace)
                    trace.expressions_evaluated.append({"expr": expr, "result": bool(val)})
                    results.append(bool(val))
                return all(results)

            if when.any:
                results = []
                for expr in when.any:
                    val = evaluate_expression(expr, namespace)
                    trace.expressions_evaluated.append({"expr": expr, "result": bool(val)})
                    results.append(bool(val))
                return any(results)

            if when.expr:
                result = evaluate_expression(when.expr, namespace)
                trace.expressions_evaluated.append({"expr": when.expr, "result": bool(result)})
                return bool(result)

        return False
