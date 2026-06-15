from app.schemas.crawl import CrawlListing, CrawlResult


def crawl_listings(brand_id: int, product_id: int, country_code: str, proxy_config: dict | None) -> CrawlResult:
    _ = proxy_config

    listing = CrawlListing(
        product_id=product_id,
        seller_id=1,
        marketplace_id=1,
        seller_name="Demo Seller",
        listing_title="Demo Product Listing",
        listing_url="https://example.com/listings/demo-product",
        image_url="https://example.com/images/demo-product.jpg",
        advertised_price=99.99,
        currency_code="USD",
    )

    return CrawlResult(
        brand_id=brand_id,
        product_id=product_id,
        country_code=country_code,
        proxy_config=proxy_config,
        listings=[listing],
    )
