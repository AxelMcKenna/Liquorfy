# Liquorfy API

FastAPI backend for the Liquorfy price comparison platform.

## 📁 Project Structure

```
api/
├── app/                    # Main application code
│   ├── core/              # Core configuration (settings, logging)
│   ├── db/                # Database models and connection
│   ├── routes/            # API route handlers
│   ├── schemas/           # Pydantic schemas for validation
│   ├── scrapers/          # Web scrapers for liquor stores
│   ├── services/          # Business logic (parser_utils, etc.)
│   ├── workers/           # Background job workers
│   └── main.py           # FastAPI application entry point
│
├── alembic/               # Database migrations
├── scripts/               # Utility and maintenance scripts
│   ├── utilities/        # Database analysis tools
│   └── maintenance/      # Data cleanup scripts
│
├── docs/                  # Documentation
│   ├── DB_SCHEMA.md      # Database schema reference
│   └── *.md              # Scraper documentation
│
├── data/                  # Local data files (gitignored)
├── archived/              # Old debug scripts (can be deleted)
│
├── .env                   # Environment configuration
├── alembic.ini           # Alembic migration config
├── pyproject.toml        # Poetry dependencies
└── README.md             # This file
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Poetry (Python package manager)

### Installation

```bash
# Install dependencies
poetry install

# Set up environment variables
cp .env.example .env  # Edit with your config

# Run database migrations
poetry run alembic upgrade head

# Start the API server
poetry run uvicorn app.main:app --reload --port 8000
```

The API will be available at:
- **Local:** http://localhost:8000
- **Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 🗄️ Database

### Connection
Default: `postgresql://postgres:postgres@localhost:5432/liquorfy`

Configure via `.env`:
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/liquorfy
```

### Schema
See [docs/DB_SCHEMA.md](docs/DB_SCHEMA.md) for complete schema documentation.

**Tables:**
- `products` - Product catalog (10,578 products)
- `stores` - Store locations (23 stores)
- `prices` - Store-specific pricing (19,902 price points)
- `ingestion_runs` - Scraping job tracking

### Migrations

```bash
# Create a new migration
poetry run alembic revision -m "description"

# Run migrations
poetry run alembic upgrade head

# Rollback one migration
poetry run alembic downgrade -1
```

---

## 🕷️ Web Scrapers

### Supported Chains

| Chain | Products | Status | Categorization |
|-------|----------|--------|----------------|
| Liquor Centre | 8,868 | ✅ Active | 87.6% |
| Super Liquor | 1,329 | ✅ Active | 82.8% |
| Bottle-O | 204 | ✅ Active | Source cats |
| Liquorland | 175 | ✅ Active | 86.9% |
| Countdown | 2 | ⚠️ Limited | 100% |

### Running Scrapers

```bash
# Run a specific scraper
poetry run python -m app.scrapers.liquor_centre

# Or use the API endpoint
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{"chain": "liquor_centre"}'
```

### Category Inference

Products are automatically categorized using:
- **200+ keywords** (beer, wine, spirits, RTD, etc.)
- **100+ brand mappings**
- **28 distinct categories** with hierarchy

See `app/services/parser_utils.py` for inference logic.

---

## 🛠️ Scripts

Utility and maintenance scripts are in the `scripts/` directory.

### Database Analysis
```bash
# Full database state and schema
poetry run python scripts/utilities/analyze_db_state.py

# Liquor Centre summary
poetry run python scripts/utilities/check_liquor_centre_summary.py
```

### Maintenance
```bash
# Re-run category inference on NULL products
poetry run python scripts/maintenance/backfill_categories.py

# Clean up duplicate stores (already run)
poetry run python scripts/maintenance/cleanup_duplicate_stores.py
```

See [scripts/README.md](scripts/README.md) for detailed documentation.

---

## 📡 API Endpoints

### Products
```bash
# List products
GET /products?chain=liquor_centre&category=beer&limit=50

# Get product by ID
GET /products/{product_id}

# Search products
GET /products/search?q=steinlager
```

### Stores
```bash
# List stores
GET /stores?chain=liquor_centre

# Get store by ID
GET /stores/{store_id}

# Find nearby stores
GET /stores/nearby?lat=-36.8485&lon=174.7633&radius=5000
```

### Ingestion
```bash
# Trigger scraping job
POST /ingest
{
  "chain": "liquor_centre",
  "stores": ["beerescourt"],
  "categories": ["beer", "wine"]
}

# Get ingestion status
GET /ingest/runs
GET /ingest/runs/{run_id}
```

### Health
```bash
# Health check
GET /health
```

Full API documentation: http://localhost:8000/docs

---

## 🧪 Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest app/tests/test_scrapers.py
```

---

## 📊 Data Quality

### Current Statistics
- **Total Products:** 10,578
- **Total Stores:** 23
- **Total Prices:** 19,902
- **Chains:** 5

### Liquor Centre (Primary Chain)
- ✅ **87.6% categorized** (7,769 of 8,868 products)
- ✅ **100% brand inference**
- ✅ **~95% volume parsing**
- ✅ **~70% ABV extraction**

---

## 🔧 Development

### Code Organization

```
app/
├── core/           # Settings, config, logging
├── db/             # SQLAlchemy models, database connection
├── routes/         # FastAPI route handlers (controllers)
├── schemas/        # Pydantic models for request/response validation
├── scrapers/       # Web scraping logic per chain
├── services/       # Business logic (parsers, utilities)
└── workers/        # Background job processing
```

### Adding a New Scraper

1. Create `app/scrapers/new_chain.py`
2. Inherit from `Scraper` base class
3. Implement required methods:
   - `fetch_catalog_pages()`
   - `_parse_products_from_page()`
   - `save_to_db()`
4. Register in `app/scrapers/registry.py`
5. Add route in `app/routes/ingest.py`

See existing scrapers for examples.

### Adding New Categories

Edit `app/services/parser_utils.py`:

```python
CATEGORY_KEYWORDS = {
    "new_category": ["keyword1", "keyword2"],
}

BRAND_CATEGORY_MAP = {
    "brand_name": "new_category",
}
```

Then run:
```bash
poetry run python scripts/maintenance/backfill_categories.py
```

---

## 🚨 Common Issues

### Database Connection Error
```bash
# Check PostgreSQL is running
pg_isready

# Check connection string in .env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/liquorfy
```

### Import Errors
```bash
# Reinstall dependencies
poetry install

# Clear cache
poetry cache clear . --all
```

### Migration Issues
```bash
# Check current version
poetry run alembic current

# Reset to head
poetry run alembic upgrade head
```

---

## 📝 Environment Variables

Required in `.env`:

```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/liquorfy

# Application
APP_NAME=Liquorfy
ENV=development
DEBUG=true

# API
API_HOST=0.0.0.0
API_PORT=8000
```

---

## 🧹 Cleanup

```bash
# Remove archived debug files (safe to delete)
rm -rf archived/

# Remove __pycache__ directories
find . -type d -name __pycache__ -exec rm -rf {} +

# Remove pytest cache
rm -rf .pytest_cache
```

---

## 📚 Additional Documentation

- [Database Schema](docs/DB_SCHEMA.md) - Complete schema reference
- [Scripts Documentation](scripts/README.md) - Utility script usage
- [Bottle-O Scraper](docs/BOTTLE_O_SCRAPER.md) - Bottle-O implementation notes

---

## 🤝 Contributing

1. Follow PEP 8 style guide
2. Add type hints to all functions
3. Write docstrings for public functions
4. Add tests for new features
5. Update documentation

---

## 📄 License

[Your License Here]
