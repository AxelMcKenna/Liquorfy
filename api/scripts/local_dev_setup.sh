#!/usr/bin/env bash
# Spin up a local PostGIS DB, run migrations, and seed with test data.
# Usage: ./api/scripts/local_dev_setup.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

echo "==> Starting PostGIS container..."
docker compose -f docker-compose.dev.yml up -d db
echo "    Waiting for Postgres to be ready..."
until docker compose -f docker-compose.dev.yml exec db pg_isready -U postgres >/dev/null 2>&1; do
  sleep 1
done
echo "    Postgres is ready."

echo "==> Copying local env..."
cp api/.env.local api/.env

cd api

echo "==> Running Alembic migrations..."
python -m alembic upgrade head

echo "==> Seeding database..."
python -m app.db.seed

echo ""
echo "Done! Local dev DB is running at localhost:5432/liquorfy"
echo "Start the API with:  cd api && uvicorn app.main:app --reload"
