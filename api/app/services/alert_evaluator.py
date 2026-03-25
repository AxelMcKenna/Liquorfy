"""Evaluate active price alerts and send email notifications."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import async_transaction, get_async_session
from app.services.email import send_alert_email

logger = logging.getLogger(__name__)
settings = get_settings()


async def _get_user_email(user_id: str) -> str | None:
    """Fetch a user's email from Supabase Auth Admin API."""
    if not settings.supabase_url or not settings.supabase_service_role_key:
        return None

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.supabase_url}/auth/v1/admin/users/{user_id}",
                headers={
                    "apikey": settings.supabase_service_role_key,
                    "Authorization": f"Bearer {settings.supabase_service_role_key}",
                },
                timeout=10.0,
            )
        if resp.status_code == 200:
            return resp.json().get("email")
    except Exception:
        logger.exception("Failed to fetch email for user %s", user_id)

    return None


async def evaluate_alerts() -> int:
    """Evaluate all active price alerts against current prices.

    For each active alert:
    - Find the best (lowest) current price for the product
    - Check if threshold_price condition is met (price <= threshold)
    - Check if alert_on_promo condition is met (promo exists)
    - Skip if last_notified_price hasn't changed (suppress re-alerts)
    - Send email and update last_triggered_at / last_notified_price

    Returns the number of notifications sent.
    """
    notifications_sent = 0

    async with get_async_session() as session:
        # Fetch all active alerts with best current price per product
        result = await session.execute(
            text("""
                SELECT
                    a.id AS alert_id,
                    a.user_id,
                    a.product_id,
                    a.threshold_price,
                    a.alert_on_promo,
                    a.last_notified_price,
                    p.name AS product_name,
                    p.product_url,
                    best.effective_price,
                    best.store_name,
                    best.has_promo
                FROM price_alerts a
                JOIN products p ON p.id = a.product_id
                JOIN LATERAL (
                    SELECT
                        COALESCE(
                            CASE WHEN pr.promo_price_nzd IS NOT NULL
                                 AND (pr.promo_ends_at IS NULL OR pr.promo_ends_at > now())
                                 THEN pr.promo_price_nzd
                            END,
                            pr.price_nzd
                        ) AS effective_price,
                        s.name AS store_name,
                        (pr.promo_price_nzd IS NOT NULL
                         AND (pr.promo_ends_at IS NULL OR pr.promo_ends_at > now())
                        ) AS has_promo
                    FROM prices pr
                    JOIN stores s ON s.id = pr.store_id
                    WHERE pr.product_id = a.product_id
                      AND pr.last_seen_at > now() - INTERVAL '7 days'
                    ORDER BY COALESCE(
                        CASE WHEN pr.promo_price_nzd IS NOT NULL
                             AND (pr.promo_ends_at IS NULL OR pr.promo_ends_at > now())
                             THEN pr.promo_price_nzd
                        END,
                        pr.price_nzd
                    ) ASC
                    LIMIT 1
                ) best ON true
                WHERE a.active = true
            """)
        )
        alerts = result.mappings().all()

    if not alerts:
        logger.info("No active alerts to evaluate")
        return 0

    logger.info("Evaluating %d active alert(s)", len(alerts))

    # Cache user emails to avoid repeated API calls
    email_cache: dict[str, str | None] = {}

    for alert in alerts:
        alert_id = str(alert["alert_id"])
        user_id = str(alert["user_id"])
        threshold = float(alert["threshold_price"]) if alert["threshold_price"] is not None else None
        current_price = float(alert["effective_price"])
        last_notified = float(alert["last_notified_price"]) if alert["last_notified_price"] is not None else None

        # Check trigger conditions
        should_trigger = False

        if threshold is not None and current_price <= threshold:
            should_trigger = True

        if alert["alert_on_promo"] and alert["has_promo"]:
            should_trigger = True

        if not should_trigger:
            continue

        # Suppress re-alert if price hasn't changed
        if last_notified is not None and abs(current_price - last_notified) < 0.01:
            continue

        # Get user email
        if user_id not in email_cache:
            email_cache[user_id] = await _get_user_email(user_id)
        email = email_cache[user_id]

        if not email:
            logger.warning("No email for user %s — skipping alert %s", user_id, alert_id)
            continue

        # Send notification
        success = await send_alert_email(
            to_email=email,
            alert_id=alert_id,
            product_name=alert["product_name"],
            current_price=current_price,
            threshold_price=threshold,
            alert_on_promo=alert["alert_on_promo"],
            store_name=alert["store_name"],
            product_url=alert["product_url"],
        )

        if success:
            # Update alert state
            async with async_transaction() as session:
                await session.execute(
                    text(
                        "UPDATE price_alerts SET "
                        "last_triggered_at = :now, last_notified_price = :price, updated_at = :now "
                        "WHERE id = :aid"
                    ),
                    {
                        "aid": alert["alert_id"],
                        "now": datetime.now(tz=timezone.utc),
                        "price": current_price,
                    },
                )
            notifications_sent += 1
            logger.info(
                "Alert triggered: alert=%s product=%s price=%.2f -> %s",
                alert_id, alert["product_name"], current_price, email,
            )

    return notifications_sent


__all__ = ["evaluate_alerts"]
