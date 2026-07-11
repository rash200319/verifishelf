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

NAVIGATION_TIMEOUT_MS = 15_000
RENDER_SETTLE_MS = 9_000
SCREENSHOT_TIMEOUT_S = 10.0
VIEWPORT = {"width": 1280, "height": 900}

# Minimum rendered body text length to consider a capture "real". The
# blank-hydration-stall page (see comment below) reliably renders under 50
# chars of visible text (just the static chrome around an empty product
# slot); a genuine product page is consistently several hundred+.
MIN_RENDERED_TEXT_CHARS = 200

# Body text length alone isn't a reliable signal by itself -- the static
# nav/header chrome (login, help center, category links, ...) alone runs
# well past MIN_RENDERED_TEXT_CHARS even when the product content area
# hasn't painted at all, an unstyled-nav-only render observed directly
# during testing. The product title heading is the one thing that's both
# always present on a real render and never present on a stalled one, so
# require it too.
MIN_TITLE_TEXT_CHARS = 8
CONTENT_CHECK_TIMEOUT_S = 5.0

# Bounded, best-effort wait for the largest on-page image (the actual
# product photo, not the page's decorative chrome) to finish loading after
# the text-content check passes. RENDER_SETTLE_MS is usually enough on its
# own, but under slower proxy latency the text can be present while the
# hero image is still a few hundred ms from painting -- this closes that
# gap without waiting on "load"/networkidle, which are known to hang (see
# comment below). A miss here is non-fatal; the capture still proceeds.
IMAGE_READY_TIMEOUT_S = 3.0

# One retry on a blank capture, since this failure mode has been observed
# to be intermittent for the *same* listing/proxy session rather than a
# hard block -- see capture_listing_screenshot docstring.
MAX_ATTEMPTS = 2

# Hard ceiling on the whole capture (all attempts combined). Two attempts'
# individual timeouts can in principle add up past a minute, which is long
# enough to trip whatever's sitting in front of this request (observed as
# the frontend's proxy reporting a "socket hang up" and the user seeing a
# bare Internal Server Error, even though the backend was still working and
# the letter eventually saved). This makes the function always return
# within a bounded time -- worst case, no screenshot -- instead of letting
# an external layer kill the connection first.
OVERALL_CAPTURE_TIMEOUT_S = 40.0


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

        # Unlike goto/screenshot above, evaluate() has no built-in timeout --
        # if the page/renderer wedges after a proxy hiccup this would
        # otherwise hang the request indefinitely instead of failing
        # best-effort like everything else here.
        try:
            readiness = await asyncio.wait_for(
                page.evaluate(
                    """() => {
                        const h1 = document.querySelector('h1');
                        return {
                            bodyLen: document.body ? document.body.innerText.length : 0,
                            titleLen: h1 ? h1.innerText.trim().length : 0,
                        };
                    }"""
                ),
                timeout=CONTENT_CHECK_TIMEOUT_S,
            )
        except asyncio.TimeoutError:
            logger.info("Content-readiness check timed out; treating as a blank capture.")
            return None

        if readiness["bodyLen"] < MIN_RENDERED_TEXT_CHARS or readiness["titleLen"] < MIN_TITLE_TEXT_CHARS:
            logger.info(
                "Listing page not fully rendered (body=%d chars, title=%d chars; need >=%d/>=%d); "
                "treating as a stalled/partial capture.",
                readiness["bodyLen"],
                readiness["titleLen"],
                MIN_RENDERED_TEXT_CHARS,
                MIN_TITLE_TEXT_CHARS,
            )
            return None

        # Best-effort only -- a slow decorative image (footer badges, ad
        # slot) timing out here is fine and expected; only the hero image
        # is worth the extra wait, and even that isn't worth failing the
        # capture over.
        try:
            await asyncio.wait_for(
                page.wait_for_function(
                    """() => {
                        const imgs = Array.from(document.querySelectorAll('img'));
                        if (!imgs.length) return true;
                        const hero = imgs.reduce((a, b) =>
                            (a.naturalWidth * a.naturalHeight) >= (b.naturalWidth * b.naturalHeight) ? a : b
                        );
                        return hero.naturalWidth > 0;
                    }"""
                ),
                timeout=IMAGE_READY_TIMEOUT_S,
            )
        except asyncio.TimeoutError:
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
