import re

from app.core.marketplaces import (
    ACTIVE_COUNTRY_CODE,
    ACTIVE_MARKETPLACE_ID,
    DARAZ_BASE_URL,
    DEMO_SELLER_ID,
)
from app.schemas.crawl import CrawlListing, CrawlResult
from app.schemas.daraz import ScrapedProduct



def _parse_price(price_raw: str) -> float:
    if not price_raw:
        return 0.0
    # Daraz prices use comma thousands separators (e.g. "Rs. 21,058").
    # Strip everything except digits so currency punctuation is ignored.
    digits = re.sub(r"[^0-9]", "", price_raw)
    try:
        return float(digits) if digits else 0.0
    except ValueError:
        return 0.0


def crawl_listings(brand_id: int, product_id: int, country_code: str, proxy_config: dict | None) -> CrawlResult:
    """
    Daraz MVP adapter.

    Simulates a Daraz scrape and maps `ScrapedProduct` into `CrawlListing`.
    Track B can replace the hardcoded scrape payload with live HTTP fetching
    while this interface stays the same.
    """
    _ = proxy_config
    resolved_country = (country_code or ACTIVE_COUNTRY_CODE).strip().upper()

    # Example scraped product (Track B replaces this with live Daraz scraping)
    scraped = ScrapedProduct(
        product_id=product_id,
        variant_id=DEMO_SELLER_ID,
        title="Demo Product Listing",
        price_raw="Rs. 21,058",
        currency="LKR",
        brand="Demo Brand",
        category_path=["Electronics", "Audio"],
        main_image="https://example.com/images/demo-product.jpg",
        description="Demo description",
        country_code=resolved_country,
    )

    advertised_price = _parse_price(scraped.price_raw)

    listing = CrawlListing(
        product_id=int(scraped.product_id),
        seller_id=int(scraped.variant_id or DEMO_SELLER_ID),
        seller_identity=scraped.brand or f"daraz-seller-{scraped.variant_id}",
        marketplace_id=ACTIVE_MARKETPLACE_ID,
        seller_name=scraped.brand or "Daraz Seller",
        listing_title=scraped.title,
        listing_url=f"{DARAZ_BASE_URL}/products/{scraped.product_id}",
        image_url=str(scraped.main_image) if scraped.main_image else None,
        advertised_price=advertised_price,
        currency_code=scraped.currency or "LKR",
    )

    return CrawlResult(
        brand_id=brand_id,
        product_id=product_id,
        country_code=country_code,
        proxy_config=proxy_config,
        listings=[listing],
    )
