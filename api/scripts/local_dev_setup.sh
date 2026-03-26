#!/usr/bin/env bash
# Spin up a local PostGIS DB, run migrations, seed, and start dev API + web.
# Usage: ./api/scripts/local_dev_setup.sh
#
# Runs the dev API on port 8001 and web on an available port,
# so it won't conflict with a production API on port 8000.
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

cd api

echo "==> Running Alembic migrations..."
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/liquorfy \
SECRET_KEY=local-dev-key-not-for-production-use-12345 \
ADMIN_PASSWORD=localdev1234 \
  python -m alembic upgrade head

echo "==> Seeding database..."
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/liquorfy \
SECRET_KEY=local-dev-key-not-for-production-use-12345 \
ADMIN_PASSWORD=localdev1234 \
  python -m app.db.seed

echo ""
echo "Done! To start the dev stack (won't conflict with production on :8000):"
echo ""
echo "  # Terminal 1 — API on port 8001"
echo "  cd api && DATABASE_URL=postgresql://postgres:postgres@localhost:5433/liquorfy \\"
echo "    SECRET_KEY=local-dev-key-not-for-production-use-12345 \\"
echo "    ADMIN_PASSWORD=localdev1234 \\"
echo "    uvicorn app.main:app --reload --port 8001"
echo ""
echo "  # Terminal 2 — Web pointed at dev API"
echo "  cd web && VITE_API_URL=http://localhost:8001 npx vite"
