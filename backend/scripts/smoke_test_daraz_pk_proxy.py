"""
Standalone smoke test for the real Daraz-PK residential proxy integration
(Day 1 workstream A). No DB/Celery/FastAPI needed.

Run directly:
    cd backend
    python scripts/smoke_test_daraz_pk_proxy.py

Verifies, in order:
  1. A real PK proxy is selected from PROXY_POOL_PK (core.proxy.get_proxy_config)
  2. A live HTTP request to Daraz PK succeeds through that proxy
  3. JSON-LD listings are actually parsed out of the response (not the
     synthetic fallback listing, which would mean the request "succeeded"
     without real data -- e.g. blocked, captcha'd, or markup changed)
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/ on path for `app.*` imports

from dotenv import load_dotenv

ROOT_ENV = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ROOT_ENV, override=True)

from app.core.proxy import get_proxy_config, ProxyConfigError  # noqa: E402
from app.adapters.listing_adapter import crawl_listings, CrawlError  # noqa: E402


async def main() -> int:
    print(f"Loading proxy config from {ROOT_ENV}")
    try:
        proxy_config = get_proxy_config("PK", "torch_demo_brand")
    except ProxyConfigError as exc:
        print(f"FAILED: {exc}")
        return 1

    print(f"Selected proxy: {proxy_config['host']}:{proxy_config['port']} (country={proxy_config['country']})")

    try:
        result = await crawl_listings(
            brand_id=1,
            product_id=1,
            product_name="iPhone 13",
            country_code="PK",
            proxy_config=proxy_config,
        )
    except CrawlError as exc:
        print(f"FAILED at step '{exc.step}': {exc}")
        return 1

    print(f"Crawl succeeded. {len(result.listings)} listing(s) parsed.")
    is_fallback = len(result.listings) == 1 and result.listings[0].listing_title.endswith("- Demo Listing")
    if is_fallback:
        print(
            "WARNING: got the synthetic fallback listing, not real JSON-LD data. "
            "Daraz PK may have blocked the request, served a captcha, or changed its markup."
        )
    for listing in result.listings[:5]:
        print(f"  - {listing.listing_title} | {listing.advertised_price} {listing.currency_code} | {listing.listing_url}")

    return 2 if is_fallback else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
