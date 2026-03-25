"""Tests for price alert routes and evaluation logic."""
from __future__ import annotations

import hashlib
import hmac
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from fastapi.testclient import TestClient

_JWT_SECRET = "test-supabase-jwt-secret-at-least-32-chars"
_SECRET_KEY = "test-secret-key-that-is-at-least-32-chars-long"


def _user_token(user_id: str | None = None) -> str:
    uid = user_id or str(uuid.uuid4())
    payload = {
        "sub": uid,
        "aud": "authenticated",
        "exp": datetime.now(tz=timezone.utc) + timedelta(hours=1),
    }
    return jwt.encode(payload, _JWT_SECRET, algorithm="HS256")


def _auth_headers(user_id: str | None = None) -> dict:
    return {"Authorization": f"Bearer {_user_token(user_id)}"}


def _unsubscribe_token(alert_id: str) -> str:
    return hmac.new(
        _SECRET_KEY.encode(),
        alert_id.encode(),
        hashlib.sha256,
    ).hexdigest()[:32]


@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    monkeypatch.setenv("SUPABASE_JWT_SECRET", _JWT_SECRET)
    from app.core.config import get_settings
    get_settings.cache_clear()


@pytest.fixture
def mock_db():
    """Create mock DB sessions that return configurable results."""
    mock_session = AsyncMock()

    @asynccontextmanager
    async def mock_get_session():
        yield mock_session

    @asynccontextmanager
    async def mock_transaction():
        yield mock_session

    return mock_session, mock_get_session, mock_transaction


class TestAlertRoutes:
    """Test alert CRUD endpoints."""

    def test_create_alert_unauthenticated(self, client):
        resp = client.post("/alerts", json={
            "product_id": str(uuid.uuid4()),
            "threshold_price": 25.0,
        })
        assert resp.status_code == 401

    def test_list_alerts_unauthenticated(self, client):
        resp = client.get("/alerts")
        assert resp.status_code == 401

    def test_unsubscribe_invalid_token(self, client):
        alert_id = str(uuid.uuid4())
        resp = client.get(f"/alerts/{alert_id}/unsubscribe?token=invalid")
        assert resp.status_code == 403


class TestUnsubscribeToken:
    """Test HMAC unsubscribe token generation."""

    def test_token_consistency(self):
        from app.routes.alerts import _unsubscribe_token
        alert_id = uuid.uuid4()
        t1 = _unsubscribe_token(alert_id)
        t2 = _unsubscribe_token(alert_id)
        assert t1 == t2
        assert len(t1) == 32

    def test_different_alerts_different_tokens(self):
        from app.routes.alerts import _unsubscribe_token
        t1 = _unsubscribe_token(uuid.uuid4())
        t2 = _unsubscribe_token(uuid.uuid4())
        assert t1 != t2


class TestAlertEvaluator:
    """Test alert evaluation logic."""

    @pytest.mark.asyncio
    async def test_evaluate_no_alerts(self):
        """Should return 0 when no active alerts exist."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        with patch("app.services.alert_evaluator.get_async_session", mock_get_session):
            from app.services.alert_evaluator import evaluate_alerts
            count = await evaluate_alerts()
            assert count == 0
