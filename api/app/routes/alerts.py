"""Price alert CRUD routes."""
from __future__ import annotations

import hashlib
import hmac
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.core.user_auth import get_current_user
from app.db.session import async_transaction, get_async_session
from app.schemas.alerts import (
    AlertListResponse,
    AlertResponse,
    CreateAlertRequest,
    UpdateAlertRequest,
)
from app.services import alert_management

settings = get_settings()

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _unsubscribe_token(alert_id: UUID) -> str:
    """Generate an HMAC token for one-click unsubscribe links."""
    return hmac.new(
        settings.secret_key.encode(),
        str(alert_id).encode(),
        hashlib.sha256,
    ).hexdigest()[:32]


def _translate_integrity_error(exc: IntegrityError) -> HTTPException:
    constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
    if constraint == "ck_price_alert_active_limit":
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "You can have up to 10 active alerts. "
                "Deactivate or delete an existing alert first."
            ),
        )
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Alert violates a database constraint",
    )


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    body: CreateAlertRequest,
    user_id: UUID = Depends(get_current_user),
):
    """Create a price alert. Max 10 active alerts per user."""
    try:
        async with async_transaction() as session:
            return await alert_management.create_alert(
                session,
                user_id=user_id,
                request=body,
            )
    except alert_management.AlertProductNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except IntegrityError as exc:
        raise _translate_integrity_error(exc) from exc


@router.get("", response_model=AlertListResponse)
async def list_alerts(user_id: UUID = Depends(get_current_user)):
    """List all alerts for the current user."""
    async with get_async_session() as session:
        items = await alert_management.list_alerts(
            session,
            user_id=user_id,
        )
    return AlertListResponse(items=items)


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: UUID,
    user_id: UUID = Depends(get_current_user),
):
    """Get a single alert."""
    async with get_async_session() as session:
        try:
            return await alert_management.get_alert(
                session,
                alert_id=alert_id,
                user_id=user_id,
            )
        except alert_management.AlertNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
            ) from exc


@router.patch("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: UUID,
    body: UpdateAlertRequest,
    user_id: UUID = Depends(get_current_user),
):
    """Update an alert's threshold, promo flag, or active status."""
    try:
        async with async_transaction() as session:
            return await alert_management.update_alert(
                session,
                alert_id=alert_id,
                user_id=user_id,
                request=body,
            )
    except alert_management.AlertNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    except alert_management.InvalidAlertConditionError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except IntegrityError as exc:
        raise _translate_integrity_error(exc) from exc


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: UUID,
    user_id: UUID = Depends(get_current_user),
):
    """Delete an alert."""
    async with async_transaction() as session:
        try:
            await alert_management.delete_alert(
                session,
                alert_id=alert_id,
                user_id=user_id,
            )
        except alert_management.AlertNotFoundError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
            ) from exc


@router.get("/{alert_id}/unsubscribe")
async def unsubscribe_alert(
    alert_id: UUID,
    token: str = Query(...),
):
    """One-click unsubscribe from an alert email. No auth required - HMAC validates ownership."""
    expected = _unsubscribe_token(alert_id)
    if not hmac.compare_digest(token, expected):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token")

    async with async_transaction() as session:
        found = await alert_management.unsubscribe_alert(
            session,
            alert_id=alert_id,
        )
    if not found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found",
        )

    return {"message": "Alert deactivated successfully"}


__all__ = ["router"]
