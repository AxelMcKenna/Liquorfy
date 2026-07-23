from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, cast

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.core.auth import close_auth_redis
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import dispose_engines
from app.middleware import (
    RateLimitExceeded,
    SecurityHeadersMiddleware,
    SlowAPIMiddleware,
    _rate_limit_exceeded_handler,
    get_limiter,
)
from app.routes import alerts, auth, health, ingest, products, stores, user, worker
from app.services.cache import close_cache

configure_logging()
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield
    await close_auth_redis()
    await close_cache()
    await dispose_engines()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

# Rate limiting
limiter = get_limiter()
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    cast(Any, _rate_limit_exceeded_handler),
)
app.add_middleware(SlowAPIMiddleware)

app.include_router(alerts.router)
app.include_router(auth.router)
app.include_router(health.router)
app.include_router(products.router)
app.include_router(stores.router)
app.include_router(user.router)
app.include_router(ingest.router)
app.include_router(worker.router)

# Security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware - environment-based configuration
# Development: Allow localhost origins for testing
# Production: Only allow configured specific domains
if settings.environment == "development":
    cors_origins = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:5174",  # Vite dev server (alternate port)
        "http://localhost:3000",  # Alternative dev port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:3000",
    ]
    allow_credentials = True
else:
    # Production: Use specific domains from environment, strip whitespace
    cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
    allow_credentials = True

    # Security check: Ensure no wildcards in production with credentials
    if "*" in cors_origins and allow_credentials:
        logger.error("SECURITY ERROR: Cannot use wildcard CORS origins with credentials in production!")
        raise ValueError("Invalid CORS configuration: wildcard origins with credentials not allowed")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = request.headers.get("x-request-id", datetime.now(timezone.utc).isoformat())
    response = await call_next(request)
    response.headers["x-request-id"] = request.state.request_id
    return response


@app.exception_handler(ValidationError)
async def validation_exception_handler(_: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic validation errors and return 422 with details."""
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


__all__ = ["app"]
