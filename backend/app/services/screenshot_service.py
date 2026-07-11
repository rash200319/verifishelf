"""
Real headless-browser screenshot capture for enforcement letter evidence.

This is the platform's actual Playwright/headless-Chromium layer -- the
Daraz listing crawl itself uses a direct httpx call against Daraz's ajax
endpoint (faster and more reliable for that specific target, see
adapters/listing_adapter.py), but that means nothing in the codebase
previously exercised a real headless browser at all. This module adds one:
every enforcement letter gets a best-effort screenshot of the actual
violating listing page, captured through the same Torch residential/ISP
proxy pool used for the rest of the crawl pipeline.

Best-effort by design: a failed screenshot (proxy hiccup, page timeout,
target blocking headless browsers) must never block letter generation --
the letter is still useful without the image. Callers treat None as
"skip attaching a screenshot", not as an error.
"""
from __future__ import annotations

import asyncio
import base64
import logging

from playwright.async_api import async_playwright

from app.core.proxy import ProxyConfigError, get_proxy_config, record_proxy_result

logger = logging.getLogger(__name__)

NAVIGATION_TIMEOUT_MS = 20_000
RENDER_SETTLE_MS = 9_000
SCREENSHOT_TIMEOUT_S = 10.0
VIEWPORT = {"width": 1280, "height": 900}

# Minimum rendered body text length to consider a capture "real". The
# blank-hydration-stall page (see comment below) reliably renders under 50
# chars of visible text (just the static chrome around an empty product
# slot); a genuine product page is consistently several hundred+.
MIN_RENDERED_TEXT_CHARS = 200

# One retry on a blank capture, since this failure mode has been observed
# to be intermittent for the *same* listing/proxy session rather than a
# hard block -- see capture_listing_screenshot docstring.
MAX_ATTEMPTS = 2


async def _capture_once(browser, listing_url: str) -> bytes | None:
    """One navigation+screenshot attempt. Returns None if the page appears
    to have blank-hydration-stalled rather than actually rendered."""
    page = await browser.new_page(
        viewport=VIEWPORT,
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
    )
    try:
        # Daraz's frontend appears to blank/stall hydration when it
        # detects automation (navigator.webdriver=true is the most
        # common signal) -- observed identical blank-skeleton
        # screenshots across repeated attempts regardless of wait
        # time, even through a verified-clean residential IP. This
        # is a standard, low-cost countermeasure for that one
        # specific signal.
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )

        # "domcontentloaded"/"load" never fire on Daraz product
        # pages through this proxy within any reasonable budget
        # (observed hanging past 45s on some third-party resource
        # that never finishes). "commit" (server responded, started
        # receiving the document) plus a short settle delay for
        # visible content to paint is a deliberate trade-off: this
        # is evidence of what a shopper sees, not a pixel-perfect
        # final render.
        await page.goto(listing_url, timeout=NAVIGATION_TIMEOUT_MS, wait_until="commit")
        await page.wait_for_timeout(RENDER_SETTLE_MS)

        rendered_text_length = await page.evaluate("document.body ? document.body.innerText.length : 0")
        if rendered_text_length < MIN_RENDERED_TEXT_CHARS:
            logger.info(
                "Listing page rendered only %d chars of text (< %d threshold); "
                "treating as a blank hydration-stall capture.",
                rendered_text_length,
                MIN_RENDERED_TEXT_CHARS,
            )
            return None

        # page.screenshot() has its own internal "waiting for fonts
        # to load" stabilization step that also hangs indefinitely
        # on this target (likely a cross-origin ad/tracker iframe,
        # not a font we control). The raw CDP command bypasses that
        # stabilization wait entirely.
        cdp = await page.context.new_cdp_session(page)
        result = await asyncio.wait_for(
            cdp.send("Page.captureScreenshot", {"format": "png"}),
            timeout=SCREENSHOT_TIMEOUT_S,
        )
        return base64.b64decode(result["data"])
    finally:
        await page.close()


async def capture_listing_screenshot(
    listing_url: str | None,
    country_code: str | None,
    brand_sub_id: str | None,
) -> str | None:
    """Best-effort base64-encoded PNG screenshot of a listing page.

    Returns None (never raises) if the listing URL/country/sub-id are
    missing, no proxy pool is configured for the country, the browser
    navigation fails for any reason, or every attempt renders a blank
    hydration-stalled page (see _capture_once) -- a blank screenshot is
    worse than no screenshot, so this never returns one.
    """
    if not listing_url or not country_code or not brand_sub_id:
        return None

    try:
        proxy_config = get_proxy_config(country_code, brand_sub_id)
    except ProxyConfigError:
        logger.info("No proxy configured for %s; skipping screenshot capture.", country_code)
        return None

    proxy_server = f"http://{proxy_config['host']}:{proxy_config['port']}"
    username, _, password = proxy_config.get("auth", "").partition(":")

    screenshot_bytes: bytes | None = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                proxy={"server": proxy_server, "username": username, "password": password},
                args=["--disable-blink-features=AutomationControlled"],
            )
            try:
                for attempt in range(1, MAX_ATTEMPTS + 1):
                    screenshot_bytes = await _capture_once(browser, listing_url)
                    if screenshot_bytes is not None:
                        break
                    logger.info(
                        "Blank capture attempt %d/%d for %s", attempt, MAX_ATTEMPTS, listing_url
                    )
            finally:
                await browser.close()
    except Exception:
        logger.exception("Screenshot capture failed for %s", listing_url)
        record_proxy_result(proxy_config, success=False)
        return None

    # A proxy session that only ever returns the blank-stall page is exactly
    # as unhealthy as one that fails outright -- recording it as a success
    # (the previous behavior) let a flagged session sit at the top of the
    # deterministic pick forever instead of rotating out after a couple of
    # bad results.
    record_proxy_result(proxy_config, success=screenshot_bytes is not None)
    if screenshot_bytes is None:
        return None
    return base64.b64encode(screenshot_bytes).decode("ascii")
