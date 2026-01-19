from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import async_transaction
from app.services.cache import get_redis_client

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthcheck() -> dict[str, str]:
    """
    Basic liveness probe - returns OK if the application is running.
    Used by container orchestrators to know if the container is alive.
    """
    return {"status": "ok"}


@router.get("/health")
async def health() -> JSONResponse:
    """
    Comprehensive health check that verifies all dependencies.
    Checks: Database, Redis, and overall application health.
    Returns 200 if all checks pass, 503 if any check fails.
    """
    health_status: Dict[str, Any] = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {},
    }

    overall_healthy = True

    # Check database connectivity
    try:
        async with async_transaction() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful",
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
        }
        overall_healthy = False

    # Check Redis connectivity using shared connection pool
    try:
        redis_client = await get_redis_client()
        await redis_client.ping()
        health_status["checks"]["redis"] = {
            "status": "healthy",
            "message": "Redis connection successful",
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}",
        }
        overall_healthy = False

    # Update overall status
    if not overall_healthy:
        health_status["status"] = "unhealthy"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status,
        )

    return JSONResponse(status_code=status.HTTP_200_OK, content=health_status)


@router.get("/readiness")
async def readiness() -> JSONResponse:
    """
    Readiness probe - checks if the application is ready to serve traffic.
    Similar to /health but may include additional application-specific checks.
    Returns 200 if ready, 503 if not ready.
    """
    readiness_status: Dict[str, Any] = {
        "status": "ready",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {},
    }

    overall_ready = True

    # Check database connectivity
    try:
        async with async_transaction() as session:
            result = await session.execute(text("SELECT 1"))
            result.scalar()
        readiness_status["checks"]["database"] = {"status": "ready"}
    except Exception as e:
        logger.error(f"Database readiness check failed: {e}")
        readiness_status["checks"]["database"] = {"status": "not_ready"}
        overall_ready = False

    # Check Redis connectivity using shared connection pool
    try:
        redis_client = await get_redis_client()
        await redis_client.ping()
        readiness_status["checks"]["redis"] = {"status": "ready"}
    except Exception as e:
        logger.error(f"Redis readiness check failed: {e}")
        readiness_status["checks"]["redis"] = {"status": "not_ready"}
        overall_ready = False

    # Update overall status
    if not overall_ready:
        readiness_status["status"] = "not_ready"
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=readiness_status,
        )

    return JSONResponse(status_code=status.HTTP_200_OK, content=readiness_status)
