ARG UV_VERSION=0.11.26
FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv
FROM python:3.11-slim

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/api \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=uv /uv /uvx /bin/

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

COPY api ./api

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
