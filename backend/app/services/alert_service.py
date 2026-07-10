"""
Best-effort violation alert notifications -- Slack webhook and/or email.

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
import smtplib
from email.message import EmailMessage

import httpx

logger = logging.getLogger(__name__)


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
    smtp_host = os.getenv("SMTP_HOST")
    alert_to = os.getenv("ALERT_EMAIL_TO")
    if not smtp_host or not alert_to:
        return False

    message = EmailMessage()
    message["Subject"] = f"MAP violation detected - {context.get('product_name')}"
    message["From"] = os.getenv("SMTP_FROM", "alerts@verifishelf.local")
    message["To"] = alert_to
    message.set_content(_format_message(context))

    try:
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            smtp_user = os.getenv("SMTP_USER")
            smtp_password = os.getenv("SMTP_PASSWORD")
            if smtp_user and smtp_password:
                server.starttls()
                server.login(smtp_user, smtp_password)
            server.send_message(message)
        return True
    except Exception:
        logger.exception("Email alert failed for violation %s", context.get("violation_id"))
        return False


def send_violation_alert(context: dict) -> None:
    """Fire whichever alert channel(s) are configured. Never raises."""
    _send_slack_alert(context)
    _send_email_alert(context)
