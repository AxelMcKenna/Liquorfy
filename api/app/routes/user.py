"""User preferences and account management routes."""
from __future__ import annotations

import logging
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text

from app.core.config import get_settings
from app.core.user_auth import get_current_user
from app.db.session import async_transaction, get_async_session
from app.schemas.user import UserPreferencesResponse, UserPreferencesUpdate

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/preferences", response_model=UserPreferencesResponse)
async def get_preferences(user_id: UUID = Depends(get_current_user)):
    """Get the current user's preferences."""
    async with get_async_session() as session:
        result = await session.execute(
            text(
                "SELECT user_id, default_lat, default_lng, default_radius_km, "
                "preferred_stores, created_at, updated_at "
                "FROM user_preferences WHERE user_id = :uid"
            ),
            {"uid": user_id},
        )
        row = result.mappings().first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No preferences found",
        )

    return UserPreferencesResponse(
        user_id=row["user_id"],
        default_lat=row["default_lat"],
        default_lng=row["default_lng"],
        default_radius_km=row["default_radius_km"],
        preferred_stores=row["preferred_stores"] or [],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.put("/preferences", response_model=UserPreferencesResponse)
async def upsert_preferences(
    body: UserPreferencesUpdate,
    user_id: UUID = Depends(get_current_user),
):
    """Create or update the current user's preferences."""
    async with async_transaction() as session:
        result = await session.execute(
            text(
                "INSERT INTO user_preferences "
                "(user_id, default_lat, default_lng, default_radius_km, preferred_stores, updated_at) "
                "VALUES (:uid, :lat, :lng, :radius, :stores, now()) "
                "ON CONFLICT (user_id) DO UPDATE SET "
                "default_lat = EXCLUDED.default_lat, "
                "default_lng = EXCLUDED.default_lng, "
                "default_radius_km = EXCLUDED.default_radius_km, "
                "preferred_stores = EXCLUDED.preferred_stores, "
                "updated_at = now() "
                "RETURNING user_id, default_lat, default_lng, default_radius_km, "
                "preferred_stores, created_at, updated_at"
            ),
            {
                "uid": user_id,
                "lat": body.default_lat,
                "lng": body.default_lng,
                "radius": body.default_radius_km,
                "stores": body.preferred_stores,
            },
        )
        row = result.mappings().first()

    return UserPreferencesResponse(
        user_id=row["user_id"],
        default_lat=row["default_lat"],
        default_lng=row["default_lng"],
        default_radius_km=row["default_radius_km"],
        preferred_stores=row["preferred_stores"] or [],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(user_id: UUID = Depends(get_current_user)):
    """Delete the current user's account and all associated data.

    Calls the Supabase Admin API to delete the auth user.
    FK cascade on user_preferences and price_alerts handles data cleanup.
    """
    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Account deletion is not configured",
        )

    async with httpx.AsyncClient() as client:
        resp = await client.delete(
            f"{settings.supabase_url}/auth/v1/admin/users/{user_id}",
            headers={
                "apikey": settings.supabase_service_role_key,
                "Authorization": f"Bearer {settings.supabase_service_role_key}",
            },
        )

    if resp.status_code >= 400:
        logger.error("Supabase account deletion failed: %s %s", resp.status_code, resp.text)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to delete account",
        )


__all__ = ["router"]
