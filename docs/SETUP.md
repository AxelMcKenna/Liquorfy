# Liquorfy Setup Guide

This guide walks you through setting up and testing the Liquorfy application.

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Poetry (Python package manager)

## Quick Start

### 1. Start Services

Start PostgreSQL and Redis using Docker Compose:

```bash
cd infra
docker-compose up -d db redis
```

This starts:
- PostgreSQL on port 5432
- Redis on port 6379

### 2. Install Dependencies

```bash
poetry install
```

### 3. Run Database Migrations

```bash
cd api
poetry run alembic upgrade head
```

This creates all the necessary database tables (stores, products, prices, ingestion_runs).

### 4. Seed Store Data

Load initial store locations for NZ liquor chains:

```bash
poetry run python scripts/seed_stores.py
```

This populates the database with ~25 store locations across major NZ cities.

### 5. Run a Scraper

Test the pipeline by running a scraper with fixture data:

```bash
poetry run python scripts/run_scraper.py countdown
```

Or test the full pipeline:

```bash
poetry run python scripts/test_pipeline.py
```

### 6. Start the API Server

```bash
cd api
poetry run uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

### 7. Start the Frontend

```bash
cd web
npm install
npm run dev
```

The web app will be available at http://localhost:5173

## Manual Testing

### Check Database Contents

Connect to PostgreSQL:

```bash
docker exec -it infra-db-1 psql -U postgres -d liquorfy
```

Query data:

```sql
-- Count stores
SELECT chain, COUNT(*) FROM stores GROUP BY chain;

-- Count products
SELECT chain, COUNT(*) FROM products GROUP BY chain;

-- Count prices
SELECT COUNT(*) FROM prices;

-- Sample products with prices
SELECT p.name, p.chain, pr.price_nzd, s.name as store_name
FROM products p
JOIN prices pr ON p.id = pr.product_id
JOIN stores s ON pr.store_id = s.id
LIMIT 10;
```

### Test API Endpoints

```bash
# Health check
curl http://localhost:8000/healthz

# Search products
curl "http://localhost:8000/products?q=beer&category=beer"

# Find stores near Auckland
curl "http://localhost:8000/stores?lat=-36.8485&lon=174.7633&radius_km=10"
```

## Architecture Overview

### Database Schema

- **stores**: Store locations with geospatial data
- **products**: Product catalog (chain + source_product_id unique)
- **prices**: Product prices per store (supports promo pricing)
- **ingestion_runs**: Metadata for scraper runs

### Scrapers

Scrapers fetch product data and persist to the database:

- **Countdown**: ✅ Implemented
- **Liquorland**: ✅ Implemented
- **Super Liquor**: ✅ Implemented
- **New World**: 🚧 Stub
- **PaknSave**: 🚧 Stub
- **Bottle O**: 🚧 Stub
- **Liquor Centre**: 🚧 Stub
- **Glengarry**: 🚧 Stub

#### Scraper Modes

Scrapers support two modes:

1. **Fixture Mode** (default): Uses test HTML files for development
2. **HTTP Mode**: Fetches live data from retailer websites

```python
# Fixture mode (for testing)
scraper = CountdownScraper(use_fixtures=True)

# HTTP mode (for production)
scraper = CountdownScraper(use_fixtures=False)
```

### API Features

- Product search with filters (category, ABV, price, volume)
- Geospatial store lookup
- Price comparison across stores
- Promo price detection
- Pagination and sorting
- Price metrics (per 100ml, per standard drink)

## Development Workflow

### Making Schema Changes

1. Update models in `api/app/db/models.py`
2. Generate migration:
   ```bash
   cd api
   alembic revision --autogenerate -m "Description of changes"
   ```
3. Review and edit migration in `api/alembic/versions/`
4. Apply migration:
   ```bash
   alembic upgrade head
   ```

### Adding a New Scraper

1. Create `api/app/scrapers/your_chain.py`:
   ```python
   from app.scrapers.base import Scraper

   class YourChainScraper(Scraper):
       chain = "your_chain"
       catalog_urls = ["https://..."]

       async def parse_products(self, payload: str):
           # Parse HTML and return list of product dicts
           pass
   ```

2. Add fixture HTML in `api/app/scrapers/fixtures/your_chain.html`

3. Register in `api/app/scrapers/__init__.py`

4. Test with fixtures, then switch to HTTP mode

### Running Tests

```bash
poetry run pytest
```

## Troubleshooting

### Database Connection Failed

Ensure PostgreSQL is running:
```bash
docker-compose ps
```

### Migrations Out of Sync

Reset and reapply:
```bash
alembic downgrade base
alembic upgrade head
```

### No Data in Database

Run the scraper:
```bash
poetry run python scripts/run_scraper.py countdown
```

## Production Deployment

### Environment Variables

Create `.env` file:

```env
DATABASE_URL=postgresql://user:pass@host:5432/liquorfy
REDIS_URL=redis://host:6379/0
SECRET_KEY=your-secret-key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure-password
ENVIRONMENT=production
```

### Running with Docker

Full stack with Docker Compose:

```bash
docker-compose up -d
```

This starts all services: db, redis, api, worker, web

## Next Steps

See the main README for the development roadmap and planned features.
