from app.schemas.crawl import CrawlListing, CrawlResult
from app.schemas.daraz import ScrapedProduct
import re


def _parse_price(price_raw: str) -> float:
    # Remove currency symbols and separators, keep digits and dot
    if not price_raw:
        return 0.0
    s = re.sub(r"[^0-9.]", "", price_raw)
    try:
        return float(s) if s else 0.0
    except ValueError:
        return 0.0


def crawl_listings(brand_id: int, product_id: int, country_code: str, proxy_config: dict | None) -> CrawlResult:
    """
    Adapter: simulate scraping Daraz and map the Daraz `ScrapedProduct`
    into the project's `CrawlListing` schema so the rest of the pipeline
    can remain unchanged.
    """
    _ = proxy_config

    # Example scraped product (in real adapter this comes from the crawler)
    scraped = ScrapedProduct(
        product_id=product_id,
        variant_id=1,
        title="Demo Product Listing",
        price_raw="Rs. 21,058",
        currency="LKR",
        brand="Demo Brand",
        category_path=["Electronics", "Audio"],
        main_image="https://example.com/images/demo-product.jpg",
        description="Demo description",
        country_code=country_code,
    )

    advertised_price = _parse_price(scraped.price_raw)

    listing = CrawlListing(
        product_id=int(scraped.product_id),
        seller_id=int(scraped.variant_id or 1),
        marketplace_id=1,  # Daraz marketplace id (keep default for now)
        seller_name=scraped.brand or "Daraz Seller",
        listing_title=scraped.title,
        # Construct a best-effort listing URL when not provided by the scraper
        listing_url=f"https://www.daraz.lk/products/{scraped.product_id}",
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
