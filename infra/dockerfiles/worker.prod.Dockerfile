FROM python:3.11-slim

ARG DEBIAN_FRONTEND=noninteractive
ARG POETRY_VERSION=2.4.1

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/api

WORKDIR /app

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main --no-root \
    && playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*

COPY api ./api

RUN useradd --create-home --uid 1000 appuser \
    && chown -R appuser:appuser /app /ms-playwright

USER appuser

CMD ["python", "-m", "app.workers.runner"]
