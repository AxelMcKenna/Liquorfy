# Operations

> **TL;DR:** Supply production secrets, validate Compose, deploy, migrate, and check `/health`. Back up PostgreSQL before schema changes; Redis is disposable.

This is the production runbook. Local setup is in the root [README](../README.md).

## Configure

Create a production environment file:

```bash
cp .env.production.template .env
openssl rand -base64 32
```

At minimum, set:

- `SECRET_KEY` to a random value of at least 32 characters;
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB`;
- `REDIS_PASSWORD`;
- `ADMIN_USERNAME` and a bcrypt `ADMIN_PASSWORD_HASH`;
- `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and the applicable Supabase JWT
  verification secret or asymmetric signing-key configuration;
- `CORS_ORIGINS` to explicit HTTPS origins.

Do not commit `.env`. Ensure the API and worker receive the application variables through the deployment platform; Compose interpolation alone does not inject arbitrary variables into a container. Terminate TLS at the host or an upstream proxy and expose only the web entry point.

## Deploy

```bash
docker compose --env-file .env -f infra/docker-compose.prod.yml config
docker compose -f infra/docker-compose.prod.yml up -d --build
docker compose -f infra/docker-compose.prod.yml exec api \
  alembic -c api/alembic.ini upgrade head
```

The supplied Compose file is a deployment baseline, not complete infrastructure automation. It contains `web`, `api`, `scheduler`, `worker`, `db`, and `redis`, with PostgreSQL and Redis data in named volumes.

The GitHub Actions workflow tests the API, builds the web app, and publishes API/web images on `main`. Its deploy job is only a placeholder; production rollout remains infrastructure-specific.

## Verify

```bash
docker compose -f infra/docker-compose.prod.yml ps
docker compose -f infra/docker-compose.prod.yml logs --tail=100 api scheduler worker
curl -fsS http://localhost/health
```

API probes:

- `/healthz`: process liveness;
- `/health`: database and Redis dependencies;
- `/readiness`: readiness;
- `/worker/health`: scraper state (admin bearer token required);
- `/worker/runs`: recent ingestion runs (admin bearer token required);
- `/ingest/jobs`: durable queue state, attempts, and leases (admin bearer
  token required).

## Migrations

Create and review migrations locally:

```bash
uv run --frozen alembic -c api/alembic.ini revision --autogenerate -m "describe change"
uv run --frozen alembic -c api/alembic.ini upgrade head
uv run --frozen alembic -c api/alembic.ini check
```

Back up the database before production schema changes. Prefer forward fixes; downgrade only when the migration explicitly supports it and data loss is understood.

## Scrapers

Run one or more chains once:

```bash
LIQUORFY_RUN_ONCE=true uv run python -m app.workers.runner countdown
LIQUORFY_RUN_ONCE=true uv run python -m app.workers.runner countdown,new_world
```

Check `api/app/scrapers/registry.py` for valid chain names and `/worker/runs` for outcomes. A failing chain should not block healthy chains; inspect worker logs and the corresponding scraper before retrying.

Manual ingestion returns `202 Accepted` with job IDs. Inspect `GET /ingest/jobs/{job_id}` or request cancellation with `POST /ingest/jobs/{job_id}/cancel`. Failed jobs retry once with backoff by default. `LIQUORFY_SCHEDULE_HOUR` controls the nightly enqueue hour in `Pacific/Auckland`.

## Backup and rollback

Back up PostgreSQL on a schedule and test restores. Redis can be recreated and is not a substitute for a database backup.

For an application rollback, deploy the previous known-good image or commit, keep the database at the newest compatible revision, and verify all health probes. Restore the database only for confirmed data corruption or an incompatible migration.

## Security

- Keep secrets outside Git and rotate them after exposure.
- Use unique database, Redis, and admin credentials.
- Restrict production CORS to trusted origins.
- Keep admin ingestion and worker-observability endpoints private.
- Keep Supabase access tokens short-lived; the API also confirms active users
  with Supabase Auth before serving user-owned alerts or preferences.
- Run containers as non-root where supported and patch base images regularly.
- Monitor authentication failures, rate-limit events, 5xx responses, and repeated scraper failures.
- Treat retailer content as untrusted input.

Report vulnerabilities privately to the repository owner; do not open a public issue with exploit details.
