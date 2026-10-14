from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from jevops.config import Settings, get_settings
from jevops.observability import setup_logging, setup_tracing

logger = structlog.stdlib.get_logger()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    setup_logging(settings)
    setup_tracing(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logger.info("jevops.startup", environment=settings.environment)
        yield
        logger.info("jevops.shutdown")

    app = FastAPI(
        title="JevOps API",
        description="AI Decision Reliability Control Plane",
        version="0.1.0",
        lifespan=lifespan,
        debug=settings.debug,
    )

    from jevops.database.engine import create_session_factory

    app.state.settings = settings
    app.state.session_factory = create_session_factory(settings)

    from jevops.api.middleware import (
        RateLimitMiddleware,
        RequestSizeLimitMiddleware,
        SecureHeadersMiddleware,
    )

    app.add_middleware(SecureHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.security.rate_limit_per_minute)
    app.add_middleware(RequestSizeLimitMiddleware, max_size=settings.security.max_request_size_bytes)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.security.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def correlation_id_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
        response: Response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    from jevops.api.v1.router import v1_router

    app.include_router(v1_router, prefix="/v1")

    return app


app = create_app()
