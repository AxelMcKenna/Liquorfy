"""User preference persistence and validation."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PriceAlert, Store, UserPreference
from app.schemas.user import UserPreferencesResponse, UserPreferencesUpdate


class PreferencesNotFoundError(LookupError):
    pass


class UnknownPreferredStoreError(ValueError):
    pass


def to_preferences_response(
    preferences: UserPreference,
) -> UserPreferencesResponse:
    return UserPreferencesResponse(
        user_id=preferences.user_id,
        default_lat=preferences.default_lat,
        default_lng=preferences.default_lng,
        default_radius_km=preferences.default_radius_km,
        preferred_stores=preferences.preferred_stores or [],
        created_at=preferences.created_at,
        updated_at=preferences.updated_at,
    )


async def get_preferences(
    session: AsyncSession, *, user_id: UUID
) -> UserPreferencesResponse:
    preferences = await session.get(UserPreference, user_id)
    if preferences is None:
        raise PreferencesNotFoundError("No preferences found")
    return to_preferences_response(preferences)


async def upsert_preferences(
    session: AsyncSession,
    *,
    user_id: UUID,
    request: UserPreferencesUpdate,
) -> UserPreferencesResponse:
    unique_store_ids = list(dict.fromkeys(request.preferred_stores))
    if unique_store_ids:
        known_store_ids = set(
            (
                await session.scalars(
                    select(Store.id).where(Store.id.in_(unique_store_ids))
                )
            ).all()
        )
        unknown = set(unique_store_ids) - known_store_ids
        if unknown:
            raise UnknownPreferredStoreError(
                f"Unknown preferred store IDs: {', '.join(sorted(map(str, unknown)))}"
            )

    preferences = await session.get(
        UserPreference,
        user_id,
        with_for_update=True,
    )
    if preferences is None:
        preferences = UserPreference(user_id=user_id)
        session.add(preferences)

    preferences.default_lat = request.default_lat
    preferences.default_lng = request.default_lng
    preferences.default_radius_km = request.default_radius_km
    preferences.preferred_stores = unique_store_ids
    await session.flush()
    return to_preferences_response(preferences)


async def delete_user_data(session: AsyncSession, *, user_id: UUID) -> None:
    await session.execute(delete(PriceAlert).where(PriceAlert.user_id == user_id))
    await session.execute(
        delete(UserPreference).where(UserPreference.user_id == user_id)
    )


__all__ = [
    "PreferencesNotFoundError",
    "UnknownPreferredStoreError",
    "delete_user_data",
    "get_preferences",
    "to_preferences_response",
    "upsert_preferences",
]
