# Liquorfy Documentation

Complete documentation for the Liquorfy price comparison platform.

## 📚 Documentation Index

### Getting Started
- **[SETUP.md](./SETUP.md)** - Complete setup guide for local development
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Production deployment instructions
- **[SECURITY.md](./SECURITY.md)** - Security features and best practices
- **[LOAD_TESTING.md](./LOAD_TESTING.md)** - Load testing strategy and performance benchmarks

### API Documentation
See **[api/](./api/)** for complete backend documentation:
- **[README.md](./api/README.md)** - API overview and quick start
- **[SCRAPERS.md](./api/SCRAPERS.md)** - Comprehensive scraper documentation for all 10 chains
- **[DATABASE.md](./api/DATABASE.md)** - Database aggregation and statistics
- **[DB_SCHEMA.md](./api/DB_SCHEMA.md)** - Complete database schema reference
- **[STORE_COLLECTION_STATUS.md](./api/STORE_COLLECTION_STATUS.md)** - Current store collection progress
 - **[scripts/README.md](./api/scripts/README.md)** - Utility and maintenance scripts
 - **[migrations/README.md](./api/migrations/README.md)** - Alembic migrations quick note

#### Scraper-Specific Documentation
See **[api/scrapers/](./api/scrapers/)** for detailed scraper guides:
- **[GUIDE.md](./api/scrapers/GUIDE.md)** - How to build and maintain scrapers
- **[BOTTLE_O.md](./api/scrapers/BOTTLE_O.md)** - Bottle-O scraper implementation details
- **[LIQUORLAND_INVESTIGATION.md](./api/scrapers/LIQUORLAND_INVESTIGATION.md)** - Liquorland store location analysis

#### Operations & Maintenance
See **[api/operations/](./api/operations/)** for operational documentation:
- **[FAILED_GEOCODING.md](./api/operations/FAILED_GEOCODING.md)** - Geocoding issues and resolutions
- **[store_locations.md](./api/operations/store_locations.md)** - Store location data management

### Mobile App Documentation
See **[mobile/](./mobile/)** for iOS/Android app documentation:
- **[README.md](./mobile/README.md)** - Mobile app quick start guide
- **[APP_STORE_GUIDE.md](./mobile/APP_STORE_GUIDE.md)** - iOS App Store submission guide
 - **[ios/CapApp-SPM.md](./mobile/ios/CapApp-SPM.md)** - SPM dependency container notes

---

## 📁 Repository Structure

```
/Liquorfy/
├── README.md                    # Project overview
├── docs/                        # 📚 All documentation (you are here)
│   ├── SETUP.md
│   ├── DEPLOYMENT.md
│   ├── SECURITY.md
│   ├── LOAD_TESTING.md
│   ├── api/                     # API backend docs
│   │   ├── scrapers/            # Scraper implementation guides
│   │   └── operations/          # Operational/maintenance docs
│   │   ├── scripts/             # Utility/maintenance scripts docs
│   │   └── migrations/          # Alembic migrations notes
│   └── mobile/                  # Mobile app docs
│       └── ios/                 # iOS-specific docs
├── api/                         # FastAPI backend
└── web/                         # React frontend + Capacitor mobile app
```

---

## 🔍 Quick Links by Topic

### Setup & Deployment
- [Local Setup](./SETUP.md)
- [Production Deployment](./DEPLOYMENT.md)
- [Security Configuration](./SECURITY.md)

### Backend Development
- [API Overview](./api/README.md)
- [Database Schema](./api/DB_SCHEMA.md)
- [Building Scrapers](./api/scrapers/GUIDE.md)
- [Scraper Documentation](./api/SCRAPERS.md)

### Operations & Monitoring
- [Store Collection Status](./api/STORE_COLLECTION_STATUS.md)
- [Geocoding Issues](./api/operations/FAILED_GEOCODING.md)
- [Load Testing](./LOAD_TESTING.md)

### Mobile Development
- [Mobile Quick Start](./mobile/README.md)
- [App Store Submission](./mobile/APP_STORE_GUIDE.md)
- [CapApp SPM Notes](./mobile/ios/CapApp-SPM.md)

---

## 📝 Contributing to Documentation

When adding new documentation:

1. **General docs** → Place in `/docs/`
2. **API-specific** → Place in `/docs/api/`
3. **Scraper guides** → Place in `/docs/api/scrapers/`
4. **Operational guides** → Place in `/docs/api/operations/`
5. **Mobile guides** → Place in `/docs/mobile/`

Update this README when adding new documentation files.
