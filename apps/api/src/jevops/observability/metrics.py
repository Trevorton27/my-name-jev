"""Prometheus-compatible metrics via OpenTelemetry."""

from __future__ import annotations


class MetricsCollector:
    """Lightweight metrics collector. In production, integrate with OTEL metrics API."""

    def __init__(self) -> None:
        self._counters: dict[str, int] = {}
        self._histograms: dict[str, list[float]] = {}

    def increment(self, name: str, value: int = 1, labels: dict[str, str] | None = None) -> None:
        key = self._key(name, labels)
        self._counters[key] = self._counters.get(key, 0) + value

    def observe(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        key = self._key(name, labels)
        self._histograms.setdefault(key, []).append(value)

    def get_counter(self, name: str, labels: dict[str, str] | None = None) -> int:
        return self._counters.get(self._key(name, labels), 0)

    def get_histogram(self, name: str, labels: dict[str, str] | None = None) -> list[float]:
        return self._histograms.get(self._key(name, labels), [])

    def _key(self, name: str, labels: dict[str, str] | None) -> str:
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"


# Global metrics instance
metrics = MetricsCollector()
