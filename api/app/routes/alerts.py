"""Price alert CRUD routes."""
from __future__ import annotations

import hashlib
import hmac
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text

from app.core.config import get_settings
from app.core.user_auth import get_current_user
from app.db.session import async_transaction, get_async_session
from app.schemas.alerts import (
    AlertListResponse,
    AlertResponse,
    CreateAlertRequest,
    UpdateAlertRequest,
)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _unsubscribe_token(alert_id: UUID) -> str:
    """Generate an HMAC token for one-click unsubscribe links."""
    return hmac.new(
        settings.secret_key.encode(),
        str(alert_id).encode(),
        hashlib.sha256,
    ).hexdigest()[:32]


def _row_to_response(row) -> AlertResponse:
    return AlertResponse(
        id=row["id"],
        product_id=row["product_id"],
        product_name=row.get("product_name"),
        threshold_price=float(row["threshold_price"]) if row["threshold_price"] is not None else None,
        alert_on_promo=row["alert_on_promo"],
        last_triggered_at=row["last_triggered_at"],
        active=row["active"],
        created_at=row["created_at"],
    )


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    body: CreateAlertRequest,
    user_id: UUID = Depends(get_current_user),
):
    """Create a price alert. Phase 1: max 1 active alert per user."""
    # Validate product exists
    async with get_async_session() as session:
        result = await session.execute(
            text("SELECT id, name FROM products WHERE id = :pid"),
            {"pid": body.product_id},
        )
        product = result.mappings().first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )

    async with async_transaction() as session:
        # Check Phase 1 limit (1 active alert per user)
        count_result = await session.execute(
            text("SELECT count(*) AS cnt FROM price_alerts WHERE user_id = :uid AND active = true"),
            {"uid": user_id},
        )
        count = count_result.scalar_one()
        if count >= 1:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Phase 1 limit: only 1 active alert allowed. Deactivate your existing alert first.",
            )

        result = await session.execute(
            text(
                "INSERT INTO price_alerts (user_id, product_id, threshold_price, alert_on_promo) "
                "VALUES (:uid, :pid, :threshold, :promo) "
                "RETURNING id, user_id, product_id, threshold_price, alert_on_promo, "
                "last_triggered_at, active, created_at"
            ),
            {
                "uid": user_id,
                "pid": body.product_id,
                "threshold": body.threshold_price,
                "promo": body.alert_on_promo,
            },
        )
        row = result.mappings().first()

    resp = _row_to_response(row)
    resp.product_name = product["name"]
    return resp


@router.get("", response_model=AlertListResponse)
async def list_alerts(user_id: UUID = Depends(get_current_user)):
    """List all alerts for the current user."""
    async with get_async_session() as session:
        result = await session.execute(
            text(
                "SELECT a.id, a.product_id, p.name AS product_name, "
                "a.threshold_price, a.alert_on_promo, a.last_triggered_at, "
                "a.active, a.created_at "
                "FROM price_alerts a "
                "LEFT JOIN products p ON p.id = a.product_id "
                "WHERE a.user_id = :uid "
                "ORDER BY a.created_at DESC"
            ),
            {"uid": user_id},
        )
        rows = result.mappings().all()

    return AlertListResponse(items=[_row_to_response(r) for r in rows])


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: UUID,
    user_id: UUID = Depends(get_current_user),
):
    """Get a single alert."""
    async with get_async_session() as session:
        result = await session.execute(
            text(
                "SELECT a.id, a.product_id, p.name AS product_name, "
                "a.threshold_price, a.alert_on_promo, a.last_triggered_at, "
                "a.active, a.created_at "
                "FROM price_alerts a "
                "LEFT JOIN products p ON p.id = a.product_id "
                "WHERE a.id = :aid AND a.user_id = :uid"
            ),
            {"aid": alert_id, "uid": user_id},
        )
        row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    return _row_to_response(row)


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: UUID,
    body: UpdateAlertRequest,
    user_id: UUID = Depends(get_current_user),
):
    """Update an alert's threshold, promo flag, or active status."""
    updates = {}
    params: dict = {"aid": alert_id, "uid": user_id}

    if body.threshold_price is not None:
        updates["threshold_price"] = ":threshold"
        params["threshold"] = body.threshold_price
    if body.alert_on_promo is not None:
        updates["alert_on_promo"] = ":promo"
        params["promo"] = body.alert_on_promo
    if body.active is not None:
        updates["active"] = ":active"
        params["active"] = body.active

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update"
        )

    set_clause = ", ".join(f"{col} = {param}" for col, param in updates.items())
    set_clause += ", updated_at = now()"

    async with async_transaction() as session:
        result = await session.execute(
            text(
                f"UPDATE price_alerts SET {set_clause} "
                "WHERE id = :aid AND user_id = :uid "
                "RETURNING id, user_id, product_id, threshold_price, alert_on_promo, "
                "last_triggered_at, active, created_at"
            ),
            params,
        )
        row = result.mappings().first()

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")

    return _row_to_response(row)


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: UUID,
    user_id: UUID = Depends(get_current_user),
):
    """Delete an alert."""
    async with async_transaction() as session:
        result = await session.execute(
            text("DELETE FROM price_alerts WHERE id = :aid AND user_id = :uid RETURNING id"),
            {"aid": alert_id, "uid": user_id},
        )
        if not result.first():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found"
            )


@router.get("/{alert_id}/unsubscribe")
async def unsubscribe_alert(
    alert_id: UUID,
    token: str = Query(...),
):
    """One-click unsubscribe from an alert email. No auth required — HMAC validates ownership."""
    expected = _unsubscribe_token(alert_id)
    if not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")

    async with async_transaction() as session:
        await session.execute(
            text("UPDATE price_alerts SET active = false, updated_at = now() WHERE id = :aid"),
            {"aid": alert_id},
        )

    return {"message": "Alert deactivated successfully"}


__all__ = ["router"]
