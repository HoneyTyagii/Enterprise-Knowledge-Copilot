from __future__ import annotations

from opentelemetry import trace
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor


def init_tracing(app, *, service_name: str = "enterprise-knowledge-copilot"):
    """Initialize OpenTelemetry tracing.

    Note: this is a bootstrap scaffold. In later commits we can wire a full exporter
    (OTLP/Jaeger) and enrich spans with RAG context.
    """

    resource = Resource(attributes={"service.name": service_name})
    provider = TracerProvider(resource=resource)
    processor = BatchSpanProcessor(None)  # no-op placeholder (we'll add exporter later)
    provider.add_span_processor(processor)

    trace.set_tracer_provider(provider)

    # Instrument FastAPI automatically (creates spans for incoming requests)
    FastAPIInstrumentor.instrument_app(app)

    return trace.get_tracer(__name__)

