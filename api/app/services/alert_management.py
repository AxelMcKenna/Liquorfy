"""Transactional price-alert management."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PriceAlert, Product
from app.schemas.alerts import (
    AlertResponse,
    CreateAlertRequest,
    UpdateAlertRequest,
)


class AlertNotFoundError(LookupError):
    pass


class AlertProductNotFoundError(LookupError):
    pass


class InvalidAlertConditionError(ValueError):
    pass


def to_alert_response(
    alert: PriceAlert, *, product_name: str | None = None
) -> AlertResponse:
    return AlertResponse(
        id=alert.id,
        product_id=alert.product_id,
        product_name=product_name,
        threshold_price=alert.threshold_price,
        alert_on_promo=alert.alert_on_promo,
        last_triggered_at=alert.last_triggered_at,
        active=alert.active,
        created_at=alert.created_at,
    )


async def create_alert(
    session: AsyncSession,
    *,
    user_id: UUID,
    request: CreateAlertRequest,
) -> AlertResponse:
    product_name = await session.scalar(
        select(Product.name).where(Product.id == request.product_id)
    )
    if product_name is None:
        raise AlertProductNotFoundError("Product not found")

    alert = PriceAlert(
        user_id=user_id,
        product_id=request.product_id,
        threshold_price=request.threshold_price,
        alert_on_promo=request.alert_on_promo,
    )
    session.add(alert)
    await session.flush()
    return to_alert_response(alert, product_name=product_name)


async def list_alerts(
    session: AsyncSession, *, user_id: UUID
) -> list[AlertResponse]:
    result = await session.execute(
        select(PriceAlert, Product.name)
        .outerjoin(Product, Product.id == PriceAlert.product_id)
        .where(PriceAlert.user_id == user_id)
        .order_by(PriceAlert.created_at.desc())
    )
    return [
        to_alert_response(alert, product_name=product_name)
        for alert, product_name in result.all()
    ]


async def get_alert(
    session: AsyncSession, *, alert_id: UUID, user_id: UUID
) -> AlertResponse:
    result = await session.execute(
        select(PriceAlert, Product.name)
        .outerjoin(Product, Product.id == PriceAlert.product_id)
        .where(PriceAlert.id == alert_id, PriceAlert.user_id == user_id)
    )
    row = result.first()
    if row is None:
        raise AlertNotFoundError("Alert not found")
    return to_alert_response(row[0], product_name=row[1])


async def update_alert(
    session: AsyncSession,
    *,
    alert_id: UUID,
    user_id: UUID,
    request: UpdateAlertRequest,
) -> AlertResponse:
    result = await session.execute(
        select(PriceAlert, Product.name)
        .outerjoin(Product, Product.id == PriceAlert.product_id)
        .where(PriceAlert.id == alert_id, PriceAlert.user_id == user_id)
        .with_for_update()
    )
    row = result.first()
    if row is None:
        raise AlertNotFoundError("Alert not found")

    alert, product_name = row
    changed_fields = request.__fields_set__
    if not changed_fields:
        raise InvalidAlertConditionError("No fields to update")

    if "threshold_price" in changed_fields:
        alert.threshold_price = request.threshold_price
    if "alert_on_promo" in changed_fields:
        if request.alert_on_promo is None:
            raise InvalidAlertConditionError("alert_on_promo cannot be null")
        alert.alert_on_promo = request.alert_on_promo
    if "active" in changed_fields:
        if request.active is None:
            raise InvalidAlertConditionError("active cannot be null")
        alert.active = request.active

    if alert.threshold_price is None and not alert.alert_on_promo:
        raise InvalidAlertConditionError(
            "Must set either threshold_price or alert_on_promo (or both)"
        )

    await session.flush()
    return to_alert_response(alert, product_name=product_name)


async def delete_alert(
    session: AsyncSession, *, alert_id: UUID, user_id: UUID
) -> None:
    result = await session.execute(
        delete(PriceAlert)
        .where(PriceAlert.id == alert_id, PriceAlert.user_id == user_id)
        .returning(PriceAlert.id)
    )
    if result.scalar_one_or_none() is None:
        raise AlertNotFoundError("Alert not found")


async def unsubscribe_alert(session: AsyncSession, *, alert_id: UUID) -> bool:
    alert = await session.get(PriceAlert, alert_id)
    if alert is None:
        return False
    alert.active = False
    await session.flush()
    return True


__all__ = [
    "AlertNotFoundError",
    "AlertProductNotFoundError",
    "InvalidAlertConditionError",
    "create_alert",
    "delete_alert",
    "get_alert",
    "list_alerts",
    "to_alert_response",
    "unsubscribe_alert",
    "update_alert",
]
