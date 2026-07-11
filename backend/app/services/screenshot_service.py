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

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

from app.core.proxy import ProxyConfigError, get_proxy_config, record_proxy_result

logger = logging.getLogger(__name__)

NAVIGATION_TIMEOUT_MS = 15_000
SCREENSHOT_TIMEOUT_S = 10.0
VIEWPORT = {"width": 1280, "height": 900}

# The readiness check below requires a non-trivial product-title heading,
# not just aggregate body text length -- the static nav/header chrome
# (login, help center, category links, ...) alone can run past a few
# hundred characters even when the product content area hasn't painted at
# all (an unstyled-nav-only render observed directly during testing). The
# title heading is present on every real render and never on a stalled one.
#
# Actively polls (rather than a fixed sleep) for the product title AND the
# advertised price, since a fixed settle window turned out to be exactly
# the wrong tool here: measured directly against the live site, the price
# is rendered by a separate, slower fetch than the title/image and simply
# wasn't in the DOM yet at a 9s fixed wait that "looked" long enough --
# every capture before this was quietly missing the one number the letter
# exists to prove. Polling resolves the instant it's actually ready instead
# of either cutting off early or always paying a worst-case fixed wait.
READINESS_TIMEOUT_MS = 15_000

# Bounded, best-effort wait for the largest on-page image (the actual
# product photo, not the page's decorative chrome) to finish loading after
# the title/price check passes. A miss here is non-fatal; the capture still
# proceeds -- this closes the common case without waiting on "load"/
# networkidle, which are known to hang (see comment below).
IMAGE_READY_TIMEOUT_MS = 3_000

# One retry on a blank/stalled capture, since that failure mode has been
# observed to be intermittent for the *same* listing/proxy session rather
# than a hard block -- see capture_listing_screenshot docstring.
MAX_ATTEMPTS = 2

# Hard ceiling on the whole capture (all attempts combined), regardless of
# how the individual per-step timeouts above add up. This is what actually
# keeps the request bounded -- observed directly as the frontend's proxy
# reporting a "socket hang up" and the user seeing a bare Internal Server
# Error on a slow capture, even though the backend was still working and
# the letter eventually saved. Sized to comfortably fit one full realistic
# attempt (worst case: 15s nav + 15s readiness poll + 3s image + 10s
# screenshot = 43s) rather than two, since getting the price reliably once
# matters more than a second attempt at a lower bar.
OVERALL_CAPTURE_TIMEOUT_S = 50.0


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
        # receiving the document) plus actively polling for the
        # specific content that matters (below) is a deliberate
        # trade-off: this is evidence of what a shopper sees, not a
        # pixel-perfect final render.
        await page.goto(listing_url, timeout=NAVIGATION_TIMEOUT_MS, wait_until="commit")

        try:
            await page.wait_for_function(
                """() => {
                    const h1 = document.querySelector('h1');
                    if (!h1 || h1.innerText.trim().length < 8) return false;
                    const bodyText = document.body ? document.body.innerText : '';
                    return /Rs\\.?\\s?[\\d,]+|LKR\\s?[\\d,]+/.test(bodyText);
                }""",
                timeout=READINESS_TIMEOUT_MS,
            )
        except PlaywrightTimeoutError:
            logger.info(
                "Title/price never rendered within %sms; treating as a stalled/blank capture.",
                READINESS_TIMEOUT_MS,
            )
            return None

        # Best-effort only -- a slow decorative image (footer badges, ad
        # slot) timing out here is fine and expected; only the hero image
        # is worth the extra wait, and even that isn't worth failing the
        # capture over.
        try:
            await page.wait_for_function(
                """() => {
                    const imgs = Array.from(document.querySelectorAll('img'));
                    if (!imgs.length) return true;
                    const hero = imgs.reduce((a, b) =>
                        (a.naturalWidth * a.naturalHeight) >= (b.naturalWidth * b.naturalHeight) ? a : b
                    );
                    return hero.naturalWidth > 0;
                }""",
                timeout=IMAGE_READY_TIMEOUT_MS,
            )
        except PlaywrightTimeoutError:
            logger.info("Hero image still loading after grace period; capturing anyway.")

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

    async def _run_attempts() -> bytes | None:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                proxy={"server": proxy_server, "username": username, "password": password},
                args=["--disable-blink-features=AutomationControlled"],
            )
            try:
                for attempt in range(1, MAX_ATTEMPTS + 1):
                    result = await _capture_once(browser, listing_url)
                    if result is not None:
                        return result
                    logger.info(
                        "Blank capture attempt %d/%d for %s", attempt, MAX_ATTEMPTS, listing_url
                    )
            finally:
                await browser.close()
        return None

    screenshot_bytes: bytes | None = None
    try:
        screenshot_bytes = await asyncio.wait_for(_run_attempts(), timeout=OVERALL_CAPTURE_TIMEOUT_S)
    except asyncio.TimeoutError:
        logger.info("Screenshot capture exceeded the %ss overall budget for %s", OVERALL_CAPTURE_TIMEOUT_S, listing_url)
        record_proxy_result(proxy_config, success=False)
        return None
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
