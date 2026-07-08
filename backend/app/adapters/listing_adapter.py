import asyncio
import json
import re
from abc import ABC, abstractmethod
from typing import Optional
from urllib.parse import quote_plus

import httpx

from app.core.marketplaces import (
    ACTIVE_COUNTRY_CODE,
    ACTIVE_MARKETPLACE_ID,
    DEMO_SELLER_ID,
    resolve_daraz_market,
)
from app.schemas.crawl import CrawlListing, CrawlResult


class MarketplaceAdapter(ABC):
    """
    Abstract base class for marketplace adapters.
    
    This provides the marketplace abstraction readiness required for Track B.
    Each marketplace (Daraz, Amazon, Flipkart, Lazada, Tokopedia) will implement
    this interface with their specific scraping logic.
    """
    
    @abstractmethod
    async def fetch_listings(
        self,
        brand_id: int,
        product_id: int,
        product_name: str,
        country_code: str,
        proxy_config: Optional[dict] = None,
    ) -> CrawlResult:
        """
        Fetch listings from the marketplace.
        
        Args:
            brand_id: The brand ID
            product_id: The product ID
            product_name: The product name to search for
            country_code: The country code for the marketplace
            proxy_config: Optional proxy configuration
            
        Returns:
            CrawlResult containing listings and raw data
        """
        pass
    
    @abstractmethod
    def get_marketplace_id(self) -> int:
        """Return the marketplace ID for this adapter."""
        pass
    
    @abstractmethod
    def get_marketplace_name(self) -> str:
        """Return the marketplace name for this adapter."""
        pass


_PRICE_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


def _parse_price(price_raw) -> float:
    if not price_raw:
        return 0.0
    # Strip thousands separators first so "21,058" -> "21058" rather than
    # being cut at the comma; then pull out the first numeric run. A naive
    # "strip everything but digits/dots" breaks on "Rs. 21,058" (the dot in
    # "Rs." survives and shifts the decimal point) -- match a real number
    # pattern instead.
    text = str(price_raw).replace(",", "")
    match = _PRICE_NUMBER_RE.search(text)
    if not match:
        return 0.0
    try:
        return float(match.group())
    except ValueError:
        return 0.0


def _normalize_item_url(item_url: str | None, base_url: str, fallback: str) -> str:
    if not item_url:
        return fallback
    if item_url.startswith("//"):
        return f"https:{item_url}"
    if item_url.startswith("/"):
        return f"{base_url}{item_url}"
    return item_url


def _extract_listings_from_ajax_json(
    payload: dict,
    product_id: int,
    base_url: str,
    default_currency: str,
    fallback_url: str,
) -> list[CrawlListing]:
    """
    Parse Daraz's real search-results payload (the same JSON its own frontend
    fetches from `{base_url}/catalog/?ajax=true&isFirstRequest=true&page=1&q=...`,
    under `mods.listItems`).

    This replaces JSON-LD parsing: a plain HTTP GET of the search page returns
    only an empty client-rendered SPA shell with no JSON-LD or price data at
    all (confirmed against a real Daraz PK response). The ajax endpoint is the
    actual, unauthenticated, same-domain JSON API Daraz's own React frontend
    calls to render results -- it requires no signing/session and returns
    real prices, seller names, and seller IDs per listing.
    """
    listings: list[CrawlListing] = []

    list_items = payload.get("mods", {}).get("listItems") if isinstance(payload.get("mods"), dict) else None
    if not isinstance(list_items, list):
        return listings

    for item in list_items:
        if not isinstance(item, dict):
            continue

        title = str(item.get("name") or "").strip()
        if not title:
            continue

        raw_seller_id = item.get("sellerId")
        try:
            seller_id = int(raw_seller_id)
        except (TypeError, ValueError):
            seller_id = DEMO_SELLER_ID

        price = _parse_price(item.get("price")) or _parse_price(item.get("priceShow"))

        listings.append(
            CrawlListing(
                product_id=product_id,
                seller_id=seller_id,
                seller_identity=f"daraz-seller-{raw_seller_id}" if raw_seller_id else None,
                marketplace_id=ACTIVE_MARKETPLACE_ID,
                seller_name=str(item.get("sellerName") or "Daraz Seller").strip(),
                listing_title=title,
                listing_url=_normalize_item_url(item.get("itemUrl"), base_url, fallback_url),
                image_url=str(item.get("image")) if item.get("image") else None,
                advertised_price=price,
                currency_code=default_currency,
            )
        )

    return listings


def _verification_hint(text: str) -> str | None:
    """
    Detect an anti-bot block/verification wall in the response body.

    Note: a bare "verification" substring is too broad -- Daraz's normal,
    unblocked pages include a `<meta name="google-site-verification">` tag,
    which false-positived every real page as "blocked" (confirmed against a
    real Daraz PK response during the Day 1 proxy smoke test). Only specific,
    known block-page phrases are checked here.
    """
    lowered = text.lower()
    for hint in ["human verification", "captcha", "please enable javascript", "access denied", "unusual traffic"]:
        if hint in lowered:
            return hint
    return None


class CrawlError(Exception):
    def __init__(self, step: str, message: str):
        super().__init__(message)
        self.step = step


class DarazAdapter(MarketplaceAdapter):
    """
    Daraz marketplace adapter implementation.
    
    This is the concrete implementation for Daraz LK marketplace.
    Other marketplaces will have their own adapter implementations.
    """
    
    def get_marketplace_id(self) -> int:
        return ACTIVE_MARKETPLACE_ID
    
    def get_marketplace_name(self) -> str:
        return "Daraz"
    
    async def fetch_listings(
        self,
        brand_id: int,
        product_id: int,
        product_name: str,
        country_code: str,
        proxy_config: Optional[dict] = None,
    ) -> CrawlResult:
        """
        Live Daraz scraping adapter.
        Fetches Daraz search results via httpx against the real ajax search API.
        """
        return await crawl_listings(brand_id, product_id, product_name, country_code, proxy_config)


def get_marketplace_adapter(marketplace_id: int) -> MarketplaceAdapter:
    """
    Factory function to get the appropriate marketplace adapter.
    
    This provides the marketplace abstraction readiness. Currently only
    Daraz is implemented, but the pattern allows easy addition of other
    marketplaces (Amazon, Flipkart, Lazada, Tokopedia) in Track B.
    
    Args:
        marketplace_id: The marketplace ID from the marketplaces table
        
    Returns:
        A MarketplaceAdapter instance for the requested marketplace
        
    Raises:
        ValueError: If the marketplace is not supported
    """
    # Currently only Daraz (ID 1) is implemented
    # Track B will add implementations for other marketplaces
    if marketplace_id == ACTIVE_MARKETPLACE_ID:
        return DarazAdapter()
    
    # For other marketplaces, we could either:
    # 1. Raise an error (strict mode)
    # 2. Return a stub adapter that returns demo data
    # For now, we'll raise to make it clear they're not implemented
    supported_marketplaces = {
        ACTIVE_MARKETPLACE_ID: "Daraz",
        # Add more as they're implemented in Track B:
        # 2: "Amazon",
        # 3: "Flipkart",
        # 4: "Lazada",
        # 5: "Tokopedia",
    }
    
    raise ValueError(
        f"Marketplace ID {marketplace_id} is not yet implemented. "
        f"Supported marketplaces: {list(supported_marketplaces.values())}"
    )


async def crawl_listings(brand_id: int, product_id: int, product_name: str, country_code: str, proxy_config: dict | None) -> CrawlResult:
    """
    Live Daraz scraping adapter.
    Fetches Daraz search results via httpx against the real ajax search API
    (see _extract_listings_from_ajax_json for why this replaced JSON-LD parsing).

    This function is maintained for backward compatibility.
    New code should use DarazAdapter.fetch_listings() instead.
    """
    resolved_country = (country_code or ACTIVE_COUNTRY_CODE).strip().upper()
    market = resolve_daraz_market(resolved_country)
    base_url = market["base_url"]
    default_currency = market["currency"]

    proxy_url = None
    if proxy_config:
        # e.g., http://username:password@host:port
        auth = proxy_config.get("auth", "")
        host = proxy_config.get("host", "")
        port = proxy_config.get("port", "")
        if host and port:
            proxy_url = f"http://{auth}@{host}:{port}" if auth else f"http://{host}:{port}"

    search_url = f"{base_url}/catalog/?q={quote_plus(product_name)}"
    # Daraz's own React frontend fetches results from this same-domain ajax
    # endpoint (discovered by capturing the real frontend's network calls
    # through a headless browser) -- no signing/session required, and it
    # returns real prices + seller identities, unlike the SSR shell at
    # `search_url` which contains no listing data at all pre-hydration.
    ajax_url = f"{base_url}/catalog/?ajax=true&isFirstRequest=true&page=1&q={quote_plus(product_name)}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
    }

    # Transient network/proxy hiccups get a couple of quick retries; a real
    # block (403/429) or a hard HTTP error does not, since retrying those
    # just wastes proxy sessions on a request that will keep failing.
    max_attempts = 3
    raw_body: str | None = None
    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            async with httpx.AsyncClient(proxy=proxy_url, timeout=15.0) as client:
                response = await client.get(ajax_url, headers=headers)
                response.raise_for_status()
                raw_body = response.text
            break
        except httpx.ProxyError as exc:
            last_exc = CrawlError("proxy_error", str(exc))
        except httpx.TimeoutException as exc:
            last_exc = CrawlError("timeout", str(exc))
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in {403, 429}:
                raise CrawlError("upstream_blocked", f"Status {exc.response.status_code}") from exc
            raise CrawlError("http_error", str(exc)) from exc
        except Exception as exc:
            raise CrawlError("request_failed", str(exc)) from exc

        if attempt < max_attempts:
            await asyncio.sleep(0.5 * attempt)

    if raw_body is None:
        raise last_exc

    # Check for upstream blocks in the raw body
    block_hint = _verification_hint(raw_body)
    if block_hint:
        raise CrawlError("upstream_blocked", f"Hit block page: {block_hint}")

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise CrawlError("parse_error", f"Response was not valid JSON: {exc}") from exc

    try:
        listings = _extract_listings_from_ajax_json(
            payload, product_id, base_url, default_currency, fallback_url=search_url
        )
    except Exception as exc:
        raise CrawlError("parse_error", str(exc)) from exc

    # No synthetic fallback listing: a real zero-result response should
    # surface as a visible crawl failure, not silently substitute fake data
    # that could be mistaken for a real violation downstream.
    if not listings:
        raise CrawlError("no_listings_found", f"Ajax response parsed but contained no listings for '{product_name}'")

    return CrawlResult(
        brand_id=brand_id,
        product_id=product_id,
        country_code=country_code,
        proxy_config=proxy_config,
        raw_data=raw_body,
        listings=listings,
    )
