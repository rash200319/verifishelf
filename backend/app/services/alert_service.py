"""
Best-effort violation alert notifications -- Slack webhook and/or email
(via SendGrid).

These are the two channels named as concrete plan features in the pricing
tier ("email alerts" on Starter, "Slack alerts" on Growth) that previously
had no corresponding code anywhere in the platform. Both are optional and
independently configured via environment variables; neither being set is a
normal, supported state (alerts are simply skipped, logged at info level).

Fire-and-forget from the crawl pipeline: a failed or unconfigured
notification must never fail the crawl or the violation record itself, so
every function here catches broadly and returns a bool instead of raising.
"""
from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)

SENDGRID_SEND_URL = "https://api.sendgrid.com/v3/mail/send"


def _format_message(context: dict) -> str:
    delta = float(context.get("price_delta_pct") or 0)
    return (
        f"MAP violation detected for {context.get('brand_name')}\n"
        f"Product: {context.get('product_name')}\n"
        f"Seller: {context.get('seller_name')}\n"
        f"Listing: {context.get('listing_url')}\n"
        f"Advertised {context.get('advertised_price')} vs MAP {context.get('map_price')} "
        f"({delta:.1f}% below)"
    )


def _send_slack_alert(context: dict) -> bool:
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return False

    try:
        response = httpx.post(webhook_url, json={"text": f":rotating_light: {_format_message(context)}"}, timeout=10.0)
        response.raise_for_status()
        return True
    except Exception:
        logger.exception("Slack alert failed for violation %s", context.get("violation_id"))
        return False


def _send_email_alert(context: dict) -> bool:
    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("SENDGRID_FROM_EMAIL")
    alert_to = os.getenv("ALERT_EMAIL_TO")
    if not api_key or not from_email or not alert_to:
        return False

    payload = {
        "personalizations": [{"to": [{"email": alert_to}]}],
        "from": {"email": from_email},
        "subject": f"MAP violation detected - {context.get('product_name')}",
        "content": [{"type": "text/plain", "value": _format_message(context)}],
    }

    try:
        response = httpx.post(
            SENDGRID_SEND_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout=10.0,
        )
        response.raise_for_status()
        return True
    except Exception:
        logger.exception("SendGrid alert failed for violation %s", context.get("violation_id"))
        return False


def send_violation_alert(context: dict) -> None:
    """Fire whichever alert channel(s) are configured. Never raises."""
    _send_slack_alert(context)
    _send_email_alert(context)
