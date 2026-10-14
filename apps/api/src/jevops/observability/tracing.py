from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from jevops.config import Settings
from jevops.observability.metrics import metrics


def setup_tracing(settings: Settings) -> None:
    if not settings.otel.enabled:
        return

    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource.create({"service.name": settings.otel.service_name})
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=settings.otel.endpoint)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument()


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Generator[None, None, None]:
    """Lightweight span context manager. Uses OTEL if available, otherwise no-op."""
    import time

    start = time.monotonic()
    try:
        try:
            from opentelemetry import trace

            tracer = trace.get_tracer("jevops")
            with tracer.start_as_current_span(name, attributes=attributes or {}):
                yield
        except Exception:
            yield
    finally:
        elapsed_ms = (time.monotonic() - start) * 1000
        metrics.observe(f"span.{name}.duration_ms", elapsed_ms)
