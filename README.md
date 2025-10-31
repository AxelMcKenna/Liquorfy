# Liquorfy

Liquorfy surfaces the cheapest liquor options near you in New Zealand. The project includes a FastAPI backend, scraper workers, and a React frontend built with Vite and Tailwind.

## Features

- Aggregates product pricing data from major NZ supermarkets and liquor stores
- Normalises pack sizes and alcohol-by-volume (ABV) to compute price per 100ml and price per standard drink
- Supports rich filtering and search APIs
- Pluggable scraper architecture with feature flags per chain
- Redis-backed caching with graceful in-memory fallback
- Seed data and fixtures for local development

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11 (for running tests or the API locally without containers)

### Quickstart (Docker)

```bash
docker compose -f infra/docker-compose.yml up --build
```

This command starts the API (`api`), worker (`worker`), Postgres (`db`), Redis (`redis`), and the React frontend (`web`).

### Local Development

1. Copy the environment template:

    ```bash
    cp .env.example .env
    ```

2. Install dependencies (Poetry):

    ```bash
    poetry install
    ```

3. Run the API:

    ```bash
    poetry run uvicorn app.main:app --reload --app-dir api
    ```

4. Execute tests:

    ```bash
    poetry run pytest api/app/tests
    ```

### API Endpoints

- `GET /healthz`
- `GET /products`
- `GET /products/{id}`
- `GET /stores`
- `POST /ingest/run`

Interactive API docs are available at `/docs` when the API is running.

## Frontend

The React app lives under `web/` and is bootstrapped with Vite. Tailwind CSS handles styling and responsive layout.

To run locally:

```bash
cd web
npm install
npm run dev
```

## Testing

```bash
poetry run pytest api/app/tests
```

## Project Structure

```
api/        # FastAPI application, services, scrapers, tests
web/        # React frontend (Vite + Tailwind)
infra/      # Docker compose and infra scripts
```

## License

MIT
