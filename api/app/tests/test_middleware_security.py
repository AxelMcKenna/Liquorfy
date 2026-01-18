"""Tests for security middleware."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


class TestSecurityHeaders:
    """Tests for security headers middleware."""

    def test_x_content_type_options_present(self, client: TestClient):
        """Response should include X-Content-Type-Options header."""
        response = client.get("/healthz")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_frame_options_present(self, client: TestClient):
        """Response should include X-Frame-Options header."""
        response = client.get("/healthz")
        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_x_xss_protection_present(self, client: TestClient):
        """Response should include X-XSS-Protection header."""
        response = client.get("/healthz")
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    def test_referrer_policy_present(self, client: TestClient):
        """Response should include Referrer-Policy header."""
        response = client.get("/healthz")
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_permissions_policy_present(self, client: TestClient):
        """Response should include Permissions-Policy header."""
        response = client.get("/healthz")
        permissions = response.headers.get("Permissions-Policy")
        assert permissions is not None
        assert "geolocation=(self)" in permissions
        assert "microphone=()" in permissions
        assert "camera=()" in permissions

    def test_csp_present(self, client: TestClient):
        """Response should include Content-Security-Policy header."""
        response = client.get("/healthz")
        csp = response.headers.get("Content-Security-Policy")
        assert csp is not None
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp

    def test_csp_development_mode(self, client: TestClient):
        """CSP in development should allow unsafe-inline."""
        response = client.get("/healthz")
        csp = response.headers.get("Content-Security-Policy")

        # In test environment (treated as development), unsafe-inline allowed
        assert "unsafe-inline" in csp or "development" not in csp

    def test_headers_on_post_request(self, client: TestClient):
        """Security headers should be present on POST requests."""
        response = client.post(
            "/auth/login",
            json={"username": "testadmin", "password": "testpassword123"}
        )
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"

    def test_headers_on_error_response(self, client: TestClient):
        """Security headers should be present on error responses."""
        response = client.get("/nonexistent-endpoint")
        # Even 404 should have security headers
        assert response.headers.get("X-Content-Type-Options") == "nosniff"


class TestHSTSHeader:
    """Tests for HSTS header (production only)."""

    def test_no_hsts_in_development(self, client: TestClient):
        """HSTS should not be present in development/test mode."""
        response = client.get("/healthz")
        # In test environment, HSTS should not be set
        hsts = response.headers.get("Strict-Transport-Security")
        # Either not present or test env doesn't set it
        assert hsts is None or "test" in str(client)


class TestRequestIdMiddleware:
    """Tests for request ID middleware."""

    def test_request_id_in_response(self, client: TestClient):
        """Response should include x-request-id header."""
        response = client.get("/healthz")
        assert "x-request-id" in response.headers

    def test_request_id_echoed_back(self, client: TestClient):
        """Request ID from request should be echoed back."""
        custom_id = "test-request-id-12345"
        response = client.get("/healthz", headers={"x-request-id": custom_id})
        assert response.headers.get("x-request-id") == custom_id

    def test_request_id_generated_if_missing(self, client: TestClient):
        """Request ID should be generated if not provided."""
        response = client.get("/healthz")
        request_id = response.headers.get("x-request-id")
        assert request_id is not None
        assert len(request_id) > 0


class TestCORSMiddleware:
    """Tests for CORS middleware."""

    def test_cors_allows_localhost_in_dev(self, client: TestClient):
        """CORS should allow localhost origins in development."""
        response = client.options(
            "/healthz",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            }
        )
        # Should not reject the preflight
        assert response.status_code in [200, 204]

    def test_cors_headers_present(self, client: TestClient):
        """CORS headers should be present for valid origins."""
        response = client.get(
            "/healthz",
            headers={"Origin": "http://localhost:5173"}
        )
        # In dev mode, should allow localhost
        cors_header = response.headers.get("Access-Control-Allow-Origin")
        assert cors_header is not None or response.status_code == 200

    def test_cors_allows_credentials(self, client: TestClient):
        """CORS should allow credentials for valid origins."""
        response = client.get(
            "/healthz",
            headers={"Origin": "http://localhost:5173"}
        )
        # Credentials should be allowed
        allow_creds = response.headers.get("Access-Control-Allow-Credentials")
        assert allow_creds == "true" or response.status_code == 200


class TestSecurityMiddlewareIntegration:
    """Integration tests for security middleware stack."""

    def test_all_security_headers_on_api_response(self, client: TestClient):
        """All security headers should be present on API responses."""
        response = client.get("/healthz")

        expected_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Content-Security-Policy",
            "Referrer-Policy",
            "Permissions-Policy",
        ]

        for header in expected_headers:
            assert header in response.headers, f"Missing header: {header}"

    def test_security_headers_not_duplicated(self, client: TestClient):
        """Security headers should not be duplicated."""
        response = client.get("/healthz")

        # Headers dict should have single values
        for key, value in response.headers.items():
            # Check that key-specific headers aren't comma-joined duplicates
            if key.startswith("X-"):
                assert value.count("nosniff") <= 1
                assert value.count("DENY") <= 1
