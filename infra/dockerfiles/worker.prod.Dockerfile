FROM python:3.11-slim

WORKDIR /app

# System deps required by Playwright Chromium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir poetry==1.7.1

COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --only main --no-root

# Install browsers into a shared path that runtime user can read
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN poetry run playwright install chromium && \
    poetry run playwright install-deps chromium

COPY api ./api
ENV PYTHONPATH=/app/api

RUN useradd -m -u 1000 appuser && \
    mkdir -p /ms-playwright && \
    chown -R appuser:appuser /app /ms-playwright

USER appuser

CMD ["poetry", "run", "python", "-m", "app.workers.runner"]
