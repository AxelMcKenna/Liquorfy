ARG UV_VERSION=0.11.26
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv
FROM python:3.11-slim

ARG DEBIAN_FRONTEND=noninteractive

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/api \
    UVICORN_WORKERS=2 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

COPY api ./api

RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app

USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl --fail --silent http://localhost:8000/readiness || exit 1

EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers \"${UVICORN_WORKERS}\" --proxy-headers --forwarded-allow-ips='*'"]
