FROM python:3.11-slim

ARG DEBIAN_FRONTEND=noninteractive
ARG POETRY_VERSION=2.4.1

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/api \
    UVICORN_WORKERS=2

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main --no-root

COPY api ./api

RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app

USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl --fail --silent http://localhost:8000/readiness || exit 1

EXPOSE 8000

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers \"${UVICORN_WORKERS}\" --proxy-headers --forwarded-allow-ips='*'"]
