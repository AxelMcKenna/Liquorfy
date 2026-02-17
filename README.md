# Liquorfy

[![CI/CD Pipeline](https://github.com/AxelMcKenna/Liquorfy/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/AxelMcKenna/Liquorfy/actions/workflows/ci-cd.yml)
[![Production](https://img.shields.io/website?down_message=offline&label=production&up_message=online&url=https%3A%2F%2Fliquorfy.co.nz)](https://liquorfy.co.nz)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=111111)
![Vite](https://img.shields.io/badge/Vite-5-646CFF?logo=vite&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%20%2B%20PostGIS-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

Liquorfy is a location-aware liquor price comparison platform for New Zealand. It combines a FastAPI backend, scheduled scraping workers, and a React frontend to surface nearby deals with normalized pricing metrics.

Production deployment: [https://liquorfy.co.nz](https://liquorfy.co.nz)

## Table of Contents

- [Architecture](#architecture)
- [Data Flow](#data-flow)
- [Core Capabilities](#core-capabilities)
- [Getting Started](#getting-started)
- [Local Development](#local-development)
- [API Overview](#api-overview)
- [Operations and Reliability](#operations-and-reliability)
- [CI/CD](#cicd)
- [Repository Layout](#repository-layout)
- [Documentation](#documentation)

## Architecture

```mermaid
flowchart LR
  subgraph Clients
    WEB[Web App<br/>React + Vite]
    IOS[iOS App<br/>SwiftUI]
  end

  subgraph Platform
    API[FastAPI Service]
    WORKER[Worker Scheduler]
    DB[(PostgreSQL + PostGIS)]
    REDIS[(Redis Cache)]
  end

  subgraph Sources
    CHAINS[Retailer APIs and Websites]
  end

  WEB -->|HTTPS| API
  IOS -->|HTTPS| API
  API <--> DB
  API <--> REDIS
  WORKER -->|Ingest and Normalize| DB
  WORKER -->|Scrape| CHAINS
```

## Data Flow

```mermaid
flowchart TD
  A[Retailer Source Data] --> B[Chain Scrapers]
  B --> C[Normalization and Pricing Metrics]
  C --> D[(PostgreSQL + PostGIS)]
  D --> E[Search and Geospatial Services]
  E --> F[Redis Cache]
  E --> G[API Responses]
  G --> H[Web and iOS Clients]
```

## Core Capabilities

- Aggregates product and price data from major NZ liquor retailers.
- Computes standardized value metrics such as price per 100ml and price per standard drink.
- Supports geospatial store and product discovery with radius constraints.
- Provides scheduled scraper execution via a dedicated worker service.
- Includes Redis-backed response caching for high-traffic queries.
- Ships with production-minded defaults: health checks, security headers, and rate limiting.

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Node.js 20+ (for running frontend outside Docker)
- Poetry

### Quickstart (Full Stack via Docker)

```bash
cp .env.example .env
docker compose -f infra/docker-compose.yml up --build
```

Services started:

- `web` at `http://localhost:5173`
- `api` at `http://localhost:8000`
- `db` (PostgreSQL/PostGIS) on `localhost:5432`
- `redis` on `localhost:6379`
- `worker` for scheduled ingestion

### Production Stack (Docker Compose)

```bash
cp .env.production.template .env
docker compose -f infra/docker-compose.prod.yml up -d --build
```

## Local Development

### 1) Install backend dependencies

```bash
poetry install
```

### 2) Start dependencies (db + redis)

```bash
docker compose -f infra/docker-compose.yml up -d db redis
```

### 3) Run API

```bash
poetry run uvicorn app.main:app --reload --app-dir api
```

### 4) Run worker

```bash
poetry run python -m app.workers.runner
```

### 5) Run frontend

```bash
cd web
npm install
npm run dev
```

### 6) Run tests

```bash
poetry run pytest api/app/tests -v
```

## API Overview

Interactive API docs: `http://localhost:8000/docs`

In production behind Nginx, API requests are proxied under `/api`.

Core endpoints:

- `GET /healthz` - liveness probe.
- `GET /health` - dependency-aware health check (database + Redis).
- `GET /readiness` - readiness probe.
- `GET /products` - filtered and paginated product search.
- `GET /products/{product_id}` - product detail.
- `GET /stores` - geospatial nearby stores.
- `POST /auth/login` - JWT token issuance.
- `POST /auth/logout` - token revocation.
- `POST /ingest/run` - trigger ingestion (admin-protected).
- `GET /worker/health` - scraper status summary.
- `GET /worker/runs` - ingestion run history.
- `GET /worker/runs/{run_id}` - ingestion run detail.

## Operations and Reliability

- Development environment template: `.env.example`
- Production environment template: `.env.production.template`
- Production compose file: `infra/docker-compose.prod.yml`
- Container definitions: `infra/dockerfiles/`
- Nginx runtime config: `infra/nginx/nginx.conf`
- Health checks are configured at both API and container levels.
- Security middleware adds CSP and standard hardening headers.

## CI/CD

GitHub Actions workflow: `.github/workflows/ci-cd.yml`

- Runs backend tests against PostgreSQL and Redis.
- Builds the web frontend.
- Builds and pushes production Docker images to GHCR on `main`.
- Includes a deployment stage scaffold for infrastructure-specific rollout.

## Repository Layout

```text
api/          FastAPI app, services, scrapers, worker, tests
web/          React + Vite frontend
ios/          Native iOS client
infra/        Dockerfiles, Compose files, nginx config
docs/         Operational, API, and mobile documentation
```

## Documentation

- [Documentation Index](./docs/README.md)
- [Setup Guide](./docs/SETUP.md)
- [Deployment Guide](./docs/DEPLOYMENT.md)
- [Security Guide](./docs/SECURITY.md)
- [API Documentation](./docs/api/README.md)
- [Mobile Documentation](./docs/mobile/README.md)

## License

Proprietary. See [`LICENSE`](./LICENSE).
