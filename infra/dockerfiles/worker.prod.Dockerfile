ARG UV_VERSION=0.11.26
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv
FROM python:3.11-slim

ARG DEBIAN_FRONTEND=noninteractive

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/api \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=uv /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project \
    && playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*

COPY api ./api

RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app /ms-playwright

USER appuser

CMD ["python", "-m", "app.workers.runner"]
