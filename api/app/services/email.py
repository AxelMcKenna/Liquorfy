"""Email delivery via Resend for price alert notifications."""
from __future__ import annotations

import hashlib
import hmac
import logging
from html import escape

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_RESEND_API = "https://api.resend.com/emails"


def _unsubscribe_token(alert_id: str) -> str:
    """Generate an HMAC token for one-click unsubscribe."""
    return hmac.new(
        settings.secret_key.encode(),
        alert_id.encode(),
        hashlib.sha256,
    ).hexdigest()[:32]


def _render_alert_html(
    *,
    product_name: str,
    current_price: float,
    threshold_price: float | None,
    alert_on_promo: bool,
    store_name: str,
    product_url: str | None,
    unsubscribe_url: str,
) -> str:
    """Render the price alert email HTML."""
    reason = ""
    if threshold_price is not None:
        reason = f"The price dropped to <strong>${current_price:.2f}</strong> (your threshold: ${threshold_price:.2f})."
    elif alert_on_promo:
        reason = f"A new promo is available at <strong>${current_price:.2f}</strong>."

    safe_name = escape(product_name)
    safe_store = escape(store_name)

    cta = ""
    if product_url and product_url.startswith(("https://", "http://")):
        safe_url = escape(product_url, quote=True)
        cta = f'<p><a href="{safe_url}" style="display:inline-block;padding:12px 24px;background:#0d6b3b;color:#fff;text-decoration:none;border-radius:6px;">View Product</a></p>'

    return f"""
    <div style="font-family:Georgia,serif;max-width:600px;margin:0 auto;padding:24px;">
        <h2 style="color:#0d6b3b;">Price Alert: {safe_name}</h2>
        <p>{reason}</p>
        <p>Available at <strong>{safe_store}</strong>.</p>
        {cta}
        <hr style="border:none;border-top:1px solid #e5e5e5;margin:24px 0;">
        <p style="font-size:12px;color:#888;">
            <a href="{unsubscribe_url}" style="color:#888;">Unsubscribe from this alert</a>
        </p>
    </div>
    """


async def send_alert_email(
    *,
    to_email: str,
    alert_id: str,
    product_name: str,
    current_price: float,
    threshold_price: float | None,
    alert_on_promo: bool,
    store_name: str,
    product_url: str | None,
    base_url: str = "",
) -> bool:
    """Send a price alert email via Resend. Returns True on success."""
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not configured — skipping email")
        return False

    token = _unsubscribe_token(alert_id)
    api_base = base_url or settings.supabase_url.replace(".supabase.co", "")
    unsubscribe_url = f"{api_base}/alerts/{alert_id}/unsubscribe?token={token}"

    html = _render_alert_html(
        product_name=product_name,
        current_price=current_price,
        threshold_price=threshold_price,
        alert_on_promo=alert_on_promo,
        store_name=store_name,
        product_url=product_url,
        unsubscribe_url=unsubscribe_url,
    )

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                _RESEND_API,
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                json={
                    "from": settings.resend_from_email,
                    "to": [to_email],
                    "subject": f"Price Alert: {product_name}",
                    "html": html,
                },
                timeout=10.0,
            )
        if resp.status_code >= 400:
            logger.error("Resend API error: %s %s", resp.status_code, resp.text)
            return False
        return True
    except Exception:
        logger.exception("Failed to send alert email to %s", to_email)
        return False


__all__ = ["send_alert_email"]
