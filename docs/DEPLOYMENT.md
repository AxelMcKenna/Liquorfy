# Liquorfy Deployment Guide

This guide covers deploying Liquorfy to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Building Docker Images](#building-docker-images)
4. [Deployment Options](#deployment-options)
5. [Post-Deployment](#post-deployment)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)
8. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

### Required Software

- **Docker** 24.0+ and **Docker Compose** 2.20+
- **Git** for version control
- **SSL/TLS certificates** (Let's Encrypt recommended)

### Infrastructure Requirements

- **Minimum Server Specs:**
  - 4 CPU cores
  - 8GB RAM
  - 50GB disk space (SSD recommended)
  - Ubuntu 22.04 LTS or similar

- **Network:**
  - Public IP address
  - Domain name configured
  - Ports 80/443 open (HTTP/HTTPS)

- **Services:**
  - PostgreSQL 15+
  - Redis 7+
  - Reverse proxy (nginx) for SSL termination

---

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/liquorfy.git
cd liquorfy
```

### 2. Configure Environment Variables

Copy and configure the production environment template:

```bash
cp .env.production.template .env.production
```

Edit `.env.production` and set all required values:

```bash
# Generate secure secrets
openssl rand -base64 32  # For SECRET_KEY
openssl rand -base64 16  # For passwords

# Edit the file
nano .env.production
```

**Critical values to set:**
- `SECRET_KEY` - Must be 32+ characters, random
- `POSTGRES_PASSWORD` - Strong password (16+ chars)
- `REDIS_PASSWORD` - Strong password (16+ chars)
- `ADMIN_PASSWORD` - Change from default
- `CORS_ORIGINS` - Your domain(s), comma-separated

### Supabase (Optional)

If you use Supabase instead of a self-hosted Postgres instance, set `DATABASE_URL` to the Supabase connection string.

Use the **direct** connection string for long-lived services (like an OCI VM API + scrapers) and include `sslmode=require`.
Use the **pooler/transaction** string for serverless environments and include `pgbouncer=true`.

### 3. Set File Permissions

```bash
chmod 600 .env.production
```

---

## Building Docker Images

### Option 1: Build Locally

```bash
# Build API image
docker build -t liquorfy-api:latest \
  -f infra/dockerfiles/api.prod.Dockerfile .

# Build Web image
docker build -t liquorfy-web:latest \
  -f infra/dockerfiles/web.prod.Dockerfile .
```

### Option 2: Use GitHub Container Registry (Recommended)

Images are automatically built and pushed by the CI/CD pipeline on merges to `main`.

```bash
# Pull pre-built images
docker pull ghcr.io/your-org/liquorfy/api:latest
docker pull ghcr.io/your-org/liquorfy/web:latest
```

---

## Deployment Options

### Option 1: Docker Compose (Recommended for Single Server)

#### Step 1: Start Services

```bash
cd infra
docker-compose -f docker-compose.prod.yml --env-file ../.env.production up -d
```

#### Step 2: Run Database Migrations

```bash
docker-compose -f docker-compose.prod.yml exec api \
  poetry run alembic upgrade head
```

#### Step 3: Verify Deployment

```bash
# Check all services are running
docker-compose -f docker-compose.prod.yml ps

# Check API health
curl http://localhost/api/health

# Check logs
docker-compose -f docker-compose.prod.yml logs -f api
```

### Option 2: Kubernetes

See [kubernetes/README.md](./kubernetes/README.md) for Kubernetes deployment instructions.

### Option 3: Cloud Platforms

#### AWS ECS/Fargate

1. Push images to ECR
2. Create task definitions for API and Web
3. Set up Application Load Balancer
4. Configure auto-scaling

See [docs/deploy-aws.md](./docs/deploy-aws.md) for detailed steps.

#### DigitalOcean App Platform

1. Connect GitHub repository
2. Configure build settings
3. Set environment variables
4. Deploy from dashboard

See [docs/deploy-digitalocean.md](./docs/deploy-digitalocean.md) for details.

---

## Post-Deployment

### 1. Verify All Services

```bash
# Health checks
curl https://your-domain.com/api/health
curl https://your-domain.com/api/readiness
curl https://your-domain.com/api/healthz

# Check database
docker exec -it liquorfy-db psql -U postgres -d liquorfy -c "\dt"

# Check Redis
docker exec -it liquorfy-redis redis-cli ping
```

### 2. Create Admin User (if needed)

```bash
docker-compose -f docker-compose.prod.yml exec api \
  poetry run python -m app.scripts.create_admin
```

### 3. Run Initial Data Import

```bash
# Import stores
docker-compose -f docker-compose.prod.yml exec api \
  poetry run python scripts/seed_stores.py

# Run scrapers (do this in worker container for better resource management)
docker-compose -f docker-compose.prod.yml exec worker \
  poetry run python scripts/run_all_scrapers.py
```

### 4. Configure SSL/TLS

#### Using Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal is set up automatically
sudo certbot renew --dry-run
```

Update `nginx.conf` to use SSL:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # ... rest of config
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

### 5. Set Up Database Backups

```bash
# Create backup script
cat > /opt/liquorfy/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/liquorfy/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

docker exec liquorfy-db pg_dump -U postgres liquorfy | \
  gzip > $BACKUP_DIR/liquorfy_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
EOF

chmod +x /opt/liquorfy/backup.sh

# Schedule daily backups (2 AM)
echo "0 2 * * * /opt/liquorfy/backup.sh" | crontab -
```

---

## Monitoring & Maintenance

### Health Monitoring

Set up monitoring for these endpoints:

- `/health` - Overall application health
- `/readiness` - Application readiness
- `/healthz` - Basic liveness probe

Recommended tools:
- **Uptime monitoring:** UptimeRobot, Pingdom
- **APM:** New Relic, DataDog, Sentry
- **Logs:** CloudWatch, Papertrail, Loggly

### Log Management

```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f api
docker-compose -f docker-compose.prod.yml logs -f worker
docker-compose -f docker-compose.prod.yml logs -f web

# Export logs to file
docker-compose -f docker-compose.prod.yml logs --since 24h > logs_$(date +%Y%m%d).txt
```

### Database Maintenance

```bash
# Analyze database statistics
docker exec liquorfy-db psql -U postgres -d liquorfy -c "ANALYZE;"

# Vacuum database
docker exec liquorfy-db psql -U postgres -d liquorfy -c "VACUUM ANALYZE;"

# Check database size
docker exec liquorfy-db psql -U postgres -d liquorfy -c \
  "SELECT pg_size_pretty(pg_database_size('liquorfy'));"
```

### Updates and Patches

```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Restart with zero downtime (requires load balancer)
docker-compose -f docker-compose.prod.yml up -d --no-deps --scale api=2 api
docker-compose -f docker-compose.prod.yml up -d --no-deps --scale api=1 api

# Run migrations
docker-compose -f docker-compose.prod.yml exec api \
  poetry run alembic upgrade head
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs api

# Check environment variables
docker-compose -f docker-compose.prod.yml exec api env | grep DATABASE_URL

# Validate config
docker-compose -f docker-compose.prod.yml config
```

### Database Connection Errors

```bash
# Test database connectivity
docker exec liquorfy-api ping db

# Check PostgreSQL logs
docker-compose -f docker-compose.prod.yml logs db

# Verify credentials
docker exec liquorfy-db psql -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT 1;"
```

### High Memory Usage

```bash
# Check resource usage
docker stats

# Restart specific service
docker-compose -f docker-compose.prod.yml restart api

# Increase limits in docker-compose.prod.yml
```

### Scraper Failures

```bash
# Check worker logs
docker-compose -f docker-compose.prod.yml logs worker

# Test individual scraper
docker-compose -f docker-compose.prod.yml exec worker \
  poetry run python scripts/run_scraper.py countdown --limit 10

# Verify Playwright installation
docker-compose -f docker-compose.prod.yml exec worker \
  poetry run playwright --version
```

---

## Rollback Procedures

### Quick Rollback (Docker Compose)

```bash
# Stop current deployment
docker-compose -f docker-compose.prod.yml down

# Pull previous version tag
docker pull ghcr.io/your-org/liquorfy/api:previous-tag
docker pull ghcr.io/your-org/liquorfy/web:previous-tag

# Start with previous version
docker-compose -f docker-compose.prod.yml up -d
```

### Database Rollback

```bash
# Restore from backup
gunzip < /opt/liquorfy/backups/liquorfy_20240101_020000.sql.gz | \
  docker exec -i liquorfy-db psql -U postgres -d liquorfy

# Or rollback migrations
docker-compose -f docker-compose.prod.yml exec api \
  poetry run alembic downgrade -1
```

---

## Security Checklist

Before going live, verify:

- [ ] All passwords are strong and randomly generated
- [ ] `SECRET_KEY` is 32+ characters and secret
- [ ] CORS origins are set to specific domains (not `*`)
- [ ] SSL/TLS certificates are installed and working
- [ ] Firewall rules only expose ports 80/443
- [ ] Database backups are automated and tested
- [ ] Monitoring and alerting are configured
- [ ] Rate limiting is enabled (60 req/min default)
- [ ] Security headers are present (check with securityheaders.com)
- [ ] Dependencies are up to date (`poetry update`)
- [ ] Environment files (`.env.production`) are not in git
- [ ] Admin password changed from default
- [ ] Database has strong password
- [ ] Redis has authentication enabled

---

## Support

For deployment issues:

1. Check this documentation
2. Review logs: `docker-compose logs`
3. Check health endpoints: `/health`, `/readiness`
4. Create issue: https://github.com/your-org/liquorfy/issues

---

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [PostgreSQL Administration](https://www.postgresql.org/docs/15/admin.html)
- [nginx Configuration](https://nginx.org/en/docs/)
- [Let's Encrypt](https://letsencrypt.org/getting-started/)
