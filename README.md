# Liquorfy

> **TL;DR:** Run `docker compose -f infra/docker-compose.yml up --build`, then open <http://localhost:5173>. Use this file for development; use the two files in `docs/` only for architecture or production operations.

Liquorfy compares liquor prices across New Zealand retailers. The repository contains a FastAPI API and scraper worker, a React web app, and a native SwiftUI iOS app.

Production: [liquorfy.co.nz](https://liquorfy.co.nz)

## Run it

Requirements: Docker with Compose.

```bash
docker compose -f infra/docker-compose.yml up --build
```

- Web: <http://localhost:5173>
- API: <http://localhost:8000>
- API reference: <http://localhost:8000/docs>

The development stack also starts PostgreSQL, Redis, and the scraper worker.

## Develop locally

Requirements: Python 3.11, uv, and Node.js 22.

```bash
# Dependencies
uv sync
(cd web && npm install)

# Local database
docker compose -f docker-compose.dev.yml up -d db

# Host-side API configuration
export DATABASE_URL=postgresql://postgres:postgres@localhost:5433/liquorfy
export SECRET_KEY=local-dev-key-not-for-production-use-12345
export ADMIN_PASSWORD=localdev1234

# Migrate and run
uv run alembic -c api/alembic.ini upgrade head
uv run uvicorn app.main:app --reload --app-dir api

# In another terminal
(cd web && npm run dev)
```

Run the worker in another terminal:

```bash
uv run python -m app.workers.runner
```

To run selected chains once:

```bash
LIQUORFY_RUN_ONCE=true uv run python -m app.workers.runner countdown,new_world
```

Available chain names live in `api/app/scrapers/registry.py`.

## Check changes

```bash
uv run --frozen ruff check api/app api/alembic api/scripts
uv run --frozen mypy api/app
uv run --frozen alembic -c api/alembic.ini check
uv run --frozen pytest
(cd web && npm run build)
```

For the Capacitor wrapper:

```bash
(cd web && npm run cap:run:ios)
```

The separate native SwiftUI app is in `ios/` and is opened with Xcode.

## Project map

```text
api/      API, database models, scrapers, worker, and tests
web/      React/Vite web app and Capacitor wrapper
ios/      Native SwiftUI app
infra/    Docker, Compose, and Nginx configuration
docs/     Architecture and production operations
```

See [architecture](docs/ARCHITECTURE.md) for system boundaries and [operations](docs/OPERATIONS.md) for deployment, migrations, health checks, and security.

## License

Proprietary. See [LICENSE](LICENSE).
