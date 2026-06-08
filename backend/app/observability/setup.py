from __future__ import annotations

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from app.config.settings import settings
from app.observability.metrics import *  # noqa: F403
from app.observability.tracing import init_tracing


def setup_observability(app: FastAPI) -> None:
    # Metrics
    app.mount(settings.prometheus_path, make_asgi_app())

    # Tracing
    init_tracing(app, service_name=settings.otel_service_name)

