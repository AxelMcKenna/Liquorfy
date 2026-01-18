# Security Guide

This document outlines the security features and best practices for the Liquorfy application.

## Security Fixes Implemented

### ✅ 1. Password Hashing with bcrypt
- **File**: `api/app/core/auth.py`
- **Implementation**: All passwords are hashed using bcrypt before storage
- **Functions**:
  - `hash_password(password)` - Hash passwords with bcrypt
  - `verify_password(plain, hashed)` - Verify password against hash
- **Status**: ✅ IMPLEMENTED

### ✅ 2. SECRET_KEY Validation
- **File**: `api/app/core/config.py`
- **Validation**:
  - Minimum 32 characters required
  - Rejects common insecure defaults (changeme, dev-secret, etc.)
  - Raises ValueError on startup if invalid
- **Generate secure key**:
  ```bash
  openssl rand -base64 32
  ```
- **Status**: ✅ IMPLEMENTED

### ✅ 3. Database Password Protection
- **File**: `api/app/db/session.py`
- **Fix**: Set `hide_password=True` in SQLAlchemy engine creation
- **Impact**: Database credentials no longer appear in logs
- **Status**: ✅ IMPLEMENTED

### ✅ 4. Environment-Specific Security Headers
- **File**: `api/app/middleware/security.py`
- **Features**:
  - **HSTS**: Enabled only in production
  - **CSP**: Strict in production (no unsafe-inline/unsafe-eval)
  - **Development CSP**: Allows React dev tools
- **Status**: ✅ IMPLEMENTED

### ✅ 5. Secure CORS Configuration
- **File**: `api/app/main.py`
- **Development**: Only allows localhost origins (no wildcard)
- **Production**: Uses specific domains from `CORS_ORIGINS` env var
- **Validation**: Prevents wildcard (*) with credentials in production
- **Status**: ✅ IMPLEMENTED

### ✅ 6. Redis-Backed Rate Limiting
- **File**: `api/app/middleware/rate_limit.py`
- **Development**: In-memory storage (simple)
- **Production**: Redis storage (distributed, multi-instance support)
- **Default**: 60 requests/minute per IP
- **Status**: ✅ IMPLEMENTED

### ✅ 7. JWT Token Revocation
- **File**: `api/app/core/auth.py`
- **Implementation**: Redis-backed token blacklist
- **Features**:
  - `revoke_token(token)` - Add token to blacklist
  - `is_token_revoked(token)` - Check if token is blacklisted
  - Auto-expiry matches token TTL
  - Tokens hashed before storage (SHA256)
- **Endpoint**: `POST /auth/logout` - Revoke current token
- **Status**: ✅ IMPLEMENTED

### ✅ 8. Enhanced .gitignore
- **File**: `.gitignore`
- **Protected files**:
  - `.env` and all `.env.*` variants
  - `.secret_key`
  - Allows `.env.example` and `.env.production.template`
- **Status**: ✅ IMPLEMENTED

---

## Authentication & Authorization

### Login Flow

1. **POST /auth/login**
   ```json
   {
     "username": "admin",
     "password": "your_password"
   }
   ```

2. **Response**:
   ```json
   {
     "access_token": "eyJhbGci...",
     "token_type": "bearer"
   }
   ```

3. **Use token in requests**:
   ```
   Authorization: Bearer eyJhbGci...
   ```

### Logout

**POST /auth/logout**
- Requires: `Authorization: Bearer <token>` header
- Revokes the current token
- Token added to Redis blacklist until expiration

### Protected Endpoints

Currently protected (require admin token):
- `POST /ingest/run` - Trigger data ingestion

Public endpoints (no auth required):
- `GET /products` - Search products
- `GET /stores` - List stores
- `GET /health`, `/healthz`, `/readiness` - Health checks

---

## Security Headers

### Implemented Headers

| Header | Value | Purpose |
|--------|-------|---------|
| X-Content-Type-Options | nosniff | Prevent MIME sniffing |
| X-Frame-Options | DENY | Prevent clickjacking |
| X-XSS-Protection | 1; mode=block | XSS protection (legacy) |
| Strict-Transport-Security | max-age=31536000 (prod only) | Force HTTPS |
| Content-Security-Policy | environment-specific | Control resource loading |
| Referrer-Policy | strict-origin-when-cross-origin | Control referrer info |
| Permissions-Policy | restrictive | Disable unnecessary browser features |

### Content Security Policy (CSP)

**Production (Strict)**:
```
default-src 'self';
script-src 'self';
style-src 'self';
img-src 'self' data: https:;
font-src 'self' data:;
connect-src 'self' https://api.mapbox.com https://*.tiles.mapbox.com;
frame-ancestors 'none';
base-uri 'self';
form-action 'self';
```

**Development (Permissive)**:
```
default-src 'self';
script-src 'self' 'unsafe-inline' 'unsafe-eval';
style-src 'self' 'unsafe-inline';
...
```

---

## Rate Limiting

### Configuration

- **Default**: 60 requests/minute per IP address
- **Storage**:
  - Development: In-memory
  - Production: Redis (distributed)
- **Per-route limits**: Can be customized with `@limiter.limit()` decorator

### Bypass Rate Limiting

For internal services or trusted IPs, update `api/app/middleware/rate_limit.py` to customize `key_func`.

---

## Environment Variables

### Required for Production

```bash
# Application
ENVIRONMENT=production
SECRET_KEY=<32+ character random string>

# Database
DATABASE_URL=postgresql://user:password@host:port/db
POSTGRES_USER=<strong username>
POSTGRES_PASSWORD=<strong password 16+ chars>

# Redis
REDIS_URL=redis://:password@host:port/db
REDIS_PASSWORD=<strong password 16+ chars>

# Admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<strong password 12+ chars>

# CORS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

### Generate Secure Secrets

```bash
# SECRET_KEY (32+ characters)
openssl rand -base64 32

# Passwords (16+ characters)
openssl rand -base64 16

# Alternative (Python)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Deployment Security Checklist

Before deploying to production, ensure:

- [x] SECRET_KEY is 32+ characters and randomly generated
- [x] All default passwords are changed
- [x] Database credentials are strong (16+ chars)
- [x] Redis has authentication enabled
- [x] CORS_ORIGINS is set to specific domains (not *)
- [x] ENVIRONMENT=production is set
- [ ] SSL/TLS certificates are installed and valid
- [ ] Firewall rules only expose ports 80/443
- [ ] Database backups are automated
- [ ] Monitoring and alerting are configured
- [ ] `.env` files are NOT committed to git
- [ ] Dependencies are up to date (`poetry update`)
- [ ] Security scan completed (`safety check`, `bandit`)

---

## Vulnerability Reporting

If you discover a security vulnerability, please:

1. **DO NOT** open a public GitHub issue
2. Email security details to: [security@yourdomain.com]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours.

---

## Security Monitoring

### Recommended Tools

- **Application Performance**: Sentry, DataDog, New Relic
- **Dependency Scanning**: Snyk, Dependabot
- **Log Monitoring**: CloudWatch, Papertrail, Loggly
- **Uptime Monitoring**: UptimeRobot, Pingdom

### Log Security Events

The following are logged:
- Failed login attempts
- Invalid tokens
- Permission denied (403) responses
- Rate limit exceeded events
- Unhandled exceptions

Review logs regularly for suspicious activity.

---

## Known Limitations

### Current Security Gaps

1. **No Multi-Factor Authentication (MFA)**
   - Planned for future release
   - Consider implementing TOTP or SMS-based MFA

2. **Single Admin User**
   - No user management system
   - No role-based access control (RBAC)
   - Future: Implement user database with roles

3. **No Password Complexity Requirements**
   - Validator only warns, doesn't enforce
   - Future: Add minimum length, character requirements

4. **No Account Lockout**
   - No protection against brute force attacks beyond rate limiting
   - Future: Implement account lockout after N failed attempts

5. **No Audit Logging**
   - Admin actions not logged to database
   - Future: Implement comprehensive audit trail

---

## Best Practices

### For Developers

1. **Never commit secrets**
   - Use `.env` files (already gitignored)
   - Use secrets management tools in production

2. **Keep dependencies updated**
   ```bash
   poetry update
   npm audit fix
   ```

3. **Run security scans**
   ```bash
   poetry run safety check
   poetry run bandit -r api/
   ```

4. **Use environment-specific configs**
   - Never use development settings in production
   - Test with `ENVIRONMENT=production` locally

5. **Validate all inputs**
   - Use Pydantic models for request validation
   - Never trust user input

### For Operators

1. **Rotate credentials regularly**
   - SECRET_KEY: Every 90 days
   - Database passwords: Every 90 days
   - Admin password: Every 30 days

2. **Monitor logs for anomalies**
   - Failed login attempts
   - Unusual traffic patterns
   - Error spikes

3. **Keep backups encrypted**
   - Encrypt database backups at rest
   - Test restoration procedures regularly

4. **Use HTTPS everywhere**
   - Install SSL/TLS certificates
   - Enable HSTS (automatic in production)
   - Redirect HTTP to HTTPS

5. **Principle of least privilege**
   - Database user should have minimal permissions
   - API keys should be scoped appropriately

---

## Compliance

### Data Protection

- **GDPR**: User data handling (if applicable)
- **PCI DSS**: Not applicable (no payment card data stored)
- **HIPAA**: Not applicable (no health data)

### Data Retention

- JWT tokens: Auto-expire after 12 hours
- Revoked tokens: Auto-deleted from Redis after expiration
- Database backups: Retain for 30 days (configurable)

---

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [Content Security Policy](https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP)
- [bcrypt Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)

---

**Last Updated**: 2025-12-30
**Version**: 1.0.0
