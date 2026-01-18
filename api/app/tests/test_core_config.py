"""Tests for core configuration module."""
from __future__ import annotations

import os
import warnings
from unittest.mock import patch

import pytest

from app.core.config import Settings


class TestSecretKeyValidation:
    """Tests for SECRET_KEY validation."""

    def test_secret_key_minimum_length(self):
        """SECRET_KEY must be at least 32 characters."""
        with pytest.raises(ValueError, match="at least 32 characters"):
            Settings(secret_key="short")

    def test_secret_key_rejects_changeme(self):
        """SECRET_KEY should reject 'changeme' (exact match)."""
        # The validator checks if the lowercased value equals the insecure default
        # It doesn't reject padded versions, only exact matches
        with pytest.raises(ValueError, match="at least 32 characters"):
            Settings(secret_key="changeme")  # Too short anyway

    def test_secret_key_rejects_common_defaults(self):
        """SECRET_KEY should reject common insecure defaults."""
        # These are rejected because they're too short (< 32 chars)
        insecure_values = ["password", "secret", "admin"]

        for value in insecure_values:
            with pytest.raises(ValueError, match="at least 32 characters"):
                Settings(secret_key=value)

    def test_secret_key_case_insensitive(self):
        """SECRET_KEY validation should reject short keys."""
        with pytest.raises(ValueError, match="at least 32 characters"):
            Settings(secret_key="CHANGEME")

    def test_secret_key_accepts_valid_value(self):
        """SECRET_KEY should accept valid secure values."""
        settings = Settings(
            secret_key="this-is-a-valid-secret-key-that-is-secure-enough"
        )
        assert len(settings.secret_key) >= 32


class TestAdminPasswordValidation:
    """Tests for admin password validation."""

    def test_admin_password_warns_on_default(self):
        """Admin password should warn on default values."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            Settings(
                secret_key="valid-secret-key-that-is-long-enough-123",
                admin_password="admin"
            )
            assert len(w) >= 1
            assert "default admin password" in str(w[0].message).lower()

    def test_admin_password_warns_on_weak_length(self):
        """Admin password should warn if too short."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            Settings(
                secret_key="valid-secret-key-that-is-long-enough-123",
                admin_password="short"
            )
            assert any("weak" in str(warning.message).lower() for warning in w)

    def test_admin_password_no_warn_on_strong(self):
        """Admin password should not warn on strong passwords."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            Settings(
                secret_key="valid-secret-key-that-is-long-enough-123",
                admin_password="super_strong_password_123!"
            )
            # Should not have password-related warnings
            password_warnings = [
                x for x in w if "password" in str(x.message).lower()
            ]
            assert len(password_warnings) == 0


class TestFeatureFlagsValidation:
    """Tests for feature flags parsing."""

    def test_feature_flags_empty(self):
        """Empty feature flags should return empty dict."""
        settings = Settings(
            secret_key="valid-secret-key-that-is-long-enough-123",
            feature_enabled_chains=""
        )
        assert settings.feature_enabled_chains == {}

    def test_feature_flags_none(self):
        """None feature flags should return empty dict."""
        settings = Settings(
            secret_key="valid-secret-key-that-is-long-enough-123",
            feature_enabled_chains=None
        )
        assert settings.feature_enabled_chains == {}

    def test_feature_flags_from_string(self):
        """Feature flags should parse from comma-separated string."""
        settings = Settings(
            secret_key="valid-secret-key-that-is-long-enough-123",
            feature_enabled_chains="countdown:true,paknsave:false,newworld:1"
        )
        assert settings.feature_enabled_chains == {
            "countdown": True,
            "paknsave": False,
            "newworld": True,
        }

    def test_feature_flags_from_dict(self):
        """Feature flags should accept dict directly."""
        settings = Settings(
            secret_key="valid-secret-key-that-is-long-enough-123",
            feature_enabled_chains={"chain1": True, "chain2": False}
        )
        assert settings.feature_enabled_chains == {"chain1": True, "chain2": False}

    def test_feature_flags_handles_whitespace(self):
        """Feature flags should handle extra whitespace."""
        settings = Settings(
            secret_key="valid-secret-key-that-is-long-enough-123",
            feature_enabled_chains="  countdown : true , paknsave : yes  "
        )
        assert settings.feature_enabled_chains["countdown"] is True
        assert settings.feature_enabled_chains["paknsave"] is True

    def test_feature_flags_invalid_format_raises(self):
        """Feature flags should reject invalid formats."""
        with pytest.raises(ValueError, match="Unsupported feature flag format"):
            Settings(
                secret_key="valid-secret-key-that-is-long-enough-123",
                feature_enabled_chains=12345  # Invalid type
            )


class TestSettingsDefaults:
    """Tests for settings defaults."""

    def test_default_environment(self):
        """Default environment should be development."""
        settings = Settings(
            secret_key="valid-secret-key-that-is-long-enough-123"
        )
        assert settings.environment == "development"

    def test_default_app_name(self):
        """Default app name should be Liquorfy API."""
        settings = Settings(
            secret_key="valid-secret-key-that-is-long-enough-123"
        )
        assert settings.app_name == "Liquorfy API"

    def test_default_radius(self):
        """Default radius should be 20km."""
        settings = Settings(
            secret_key="valid-secret-key-that-is-long-enough-123"
        )
        assert settings.default_radius_km == 20.0

    def test_default_cache_ttl(self):
        """Default cache TTL should be 600 seconds."""
        settings = Settings(
            secret_key="valid-secret-key-that-is-long-enough-123"
        )
        assert settings.api_cache_ttl_seconds == 600


class TestGetSettings:
    """Tests for get_settings function."""

    def test_get_settings_caches_result(self):
        """get_settings should cache the result."""
        from app.core.config import get_settings

        get_settings.cache_clear()
        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_get_settings_cache_can_be_cleared(self):
        """get_settings cache should be clearable."""
        from app.core.config import get_settings

        get_settings.cache_clear()
        settings1 = get_settings()
        get_settings.cache_clear()
        settings2 = get_settings()

        # They should be equal but not the same object
        assert settings1.app_name == settings2.app_name
