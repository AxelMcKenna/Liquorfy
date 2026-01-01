"""Security middleware for FastAPI application."""
from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import get_settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    Headers added:
    - X-Content-Type-Options: Prevents MIME type sniffing
    - X-Frame-Options: Prevents clickjacking
    - X-XSS-Protection: Enables browser XSS protection
    - Strict-Transport-Security: Enforces HTTPS
    - Content-Security-Policy: Controls resource loading
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Controls browser features
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        settings = get_settings()

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking by disallowing iframe embedding
        response.headers["X-Frame-Options"] = "DENY"

        # Enable browser XSS protection (legacy, but doesn't hurt)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Enforce HTTPS for 1 year in production
        if settings.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        # Content Security Policy - environment-specific
        if settings.environment == "development":
            # Development: Allow unsafe-inline and unsafe-eval for React dev tools
            csp_directives = [
                "default-src 'self'",
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
                "style-src 'self' 'unsafe-inline'",
                "img-src 'self' data: https:",
                "font-src 'self' data:",
                "connect-src 'self' https://api.mapbox.com https://*.tiles.mapbox.com ws://localhost:* http://localhost:*",
                "frame-ancestors 'none'",
            ]
        else:
            # Production: Strict CSP without unsafe directives
            csp_directives = [
                "default-src 'self'",
                "script-src 'self'",  # No unsafe-inline or unsafe-eval
                "style-src 'self'",  # No unsafe-inline
                "img-src 'self' data: https:",
                "font-src 'self' data:",
                "connect-src 'self' https://api.mapbox.com https://*.tiles.mapbox.com",
                "frame-ancestors 'none'",
                "base-uri 'self'",  # Prevent base tag injection
                "form-action 'self'",  # Only submit forms to same origin
            ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Control referrer information sent with requests
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Control which browser features can be used
        permissions_directives = [
            "geolocation=(self)",  # Allow geolocation only from same origin
            "microphone=()",  # Disable microphone
            "camera=()",  # Disable camera
            "payment=()",  # Disable payment APIs
            "usb=()",  # Disable USB
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions_directives)

        return response


__all__ = ["SecurityHeadersMiddleware"]
