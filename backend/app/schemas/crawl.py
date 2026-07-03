from pydantic import BaseModel, Field


class CrawlListing(BaseModel):
    product_id: int
    seller_id: int
    seller_identity: str | None = None
    marketplace_id: int
    seller_name: str = Field(min_length=1, max_length=255)
    listing_title: str = Field(min_length=1)
    listing_url: str
    image_url: str | None = None
    advertised_price: float
    currency_code: str = Field(default="USD", max_length=10)


class NormalizedCrawlListing(BaseModel):
    product_id: int
    seller_id: int
    seller_identity: str | None = None
    marketplace_id: int
    seller_name: str
    listing_title: str
    listing_url: str
    image_url: str | None = None
    advertised_price: float
    currency_code: str = "USD"


class CrawlResult(BaseModel):
    brand_id: int
    product_id: int
    country_code: str
    proxy_config: dict | None = None
    listings: list[CrawlListing]


class NormalizedCrawlResult(BaseModel):
    brand_id: int
    product_id: int
    country_code: str
    proxy_config: dict | None = None
    listings: list[NormalizedCrawlListing]
