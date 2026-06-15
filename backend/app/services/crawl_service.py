import logging

from app.adapters.listing_adapter import crawl_listings
from app.core.proxy import get_proxy_config
from app.repositories.brand_repository import BrandRepository
from app.repositories.listing_repository import ListingRepository
from app.repositories.price_snapshot_repository import PriceSnapshotRepository
from app.schemas.crawl import CrawlListing, CrawlResult, NormalizedCrawlListing, NormalizedCrawlResult


logger = logging.getLogger(__name__)


class CrawlService:
    @staticmethod
    def _failure_result(
        brand_id: int,
        product_id: int,
        country_code: str,
        failed_step: str,
        error: str,
        proxy_config: dict | None = None,
        listings: list[dict] | None = None,
        price_snapshots: list[dict] | None = None,
    ):
        return {
            "status": "failed",
            "failed_step": failed_step,
            "error": error,
            "brand_id": brand_id,
            "product_id": product_id,
            "country_code": country_code,
            "proxy_config": proxy_config,
            "listings": listings or [],
            "price_snapshots": price_snapshots or [],
        }

    @staticmethod
    def _normalize_listing(crawl_listing: CrawlListing | dict) -> NormalizedCrawlListing:
        listing = crawl_listing.model_dump() if hasattr(crawl_listing, "model_dump") else dict(crawl_listing)

        return NormalizedCrawlListing(
            product_id=int(listing["product_id"]),
            seller_id=int(listing["seller_id"]),
            marketplace_id=int(listing["marketplace_id"]),
            seller_name=str(listing["seller_name"]).strip(),
            listing_title=str(listing["listing_title"]).strip(),
            listing_url=str(listing["listing_url"]).strip(),
            image_url=str(listing["image_url"]).strip() if listing.get("image_url") else None,
            advertised_price=float(listing["advertised_price"]),
            currency_code=str(listing.get("currency_code") or "USD").strip().upper(),
        )

    @classmethod
    def _normalize_result(cls, crawl_result: CrawlResult | dict) -> NormalizedCrawlResult:
        result = crawl_result.model_dump() if hasattr(crawl_result, "model_dump") else dict(crawl_result)

        normalized_listings = [cls._normalize_listing(listing) for listing in result.get("listings", [])]

        return NormalizedCrawlResult(
            brand_id=int(result["brand_id"]),
            product_id=int(result["product_id"]),
            country_code=str(result["country_code"]).strip().upper(),
            proxy_config=result.get("proxy_config"),
            listings=normalized_listings,
        )

    @staticmethod
    async def crawl_product(brand_id: int, product_id: int, country_code: str = "LK"):
        try:
            brand = await BrandRepository.get_brand_by_id(brand_id)
            if brand is None:
                return CrawlService._failure_result(
                    brand_id,
                    product_id,
                    country_code,
                    "brand_lookup",
                    f"Brand {brand_id} not found",
                )
        except Exception as exc:
            logger.exception("Brand lookup failed for brand_id=%s product_id=%s", brand_id, product_id)
            return CrawlService._failure_result(brand_id, product_id, country_code, "brand_lookup", str(exc))

        try:
            proxy_config = get_proxy_config(country_code, brand["torch_sub_id"])
        except Exception as exc:
            logger.exception("Proxy lookup failed for brand_id=%s product_id=%s", brand_id, product_id)
            return CrawlService._failure_result(brand_id, product_id, country_code, "proxy_lookup", str(exc))

        try:
            raw_result = crawl_listings(brand_id, product_id, country_code, proxy_config)
        except Exception as exc:
            logger.exception("Adapter call failed for brand_id=%s product_id=%s", brand_id, product_id)
            return CrawlService._failure_result(
                brand_id,
                product_id,
                country_code,
                "adapter_call",
                str(exc),
                proxy_config=proxy_config,
            )

        try:
            crawl_result = CrawlService._normalize_result(raw_result)
        except Exception as exc:
            logger.exception("Normalization failed for brand_id=%s product_id=%s", brand_id, product_id)
            return CrawlService._failure_result(
                brand_id,
                product_id,
                country_code,
                "normalize_result",
                str(exc),
                proxy_config=proxy_config,
            )

        saved_listings = []
        saved_snapshots = []

        for crawl_listing in crawl_result.listings:
            try:
                listing = await ListingRepository.create_listing(
                    crawl_listing.product_id,
                    crawl_listing.seller_id,
                    crawl_listing.marketplace_id,
                    crawl_listing.listing_title,
                    crawl_listing.listing_url,
                    crawl_listing.image_url,
                    crawl_listing.advertised_price,
                    crawl_listing.currency_code,
                )
            except Exception as exc:
                logger.exception("Listing insert failed for brand_id=%s product_id=%s", brand_id, product_id)
                return CrawlService._failure_result(
                    brand_id,
                    product_id,
                    country_code,
                    "listing_insert",
                    str(exc),
                    proxy_config=proxy_config,
                    listings=saved_listings,
                    price_snapshots=saved_snapshots,
                )

            try:
                snapshot = await PriceSnapshotRepository.create_price_snapshot(
                    listing["id"],
                    crawl_listing.product_id,
                    crawl_listing.seller_id,
                    crawl_listing.advertised_price,
                )
            except Exception as exc:
                logger.exception("Price snapshot insert failed for brand_id=%s product_id=%s", brand_id, product_id)
                return CrawlService._failure_result(
                    brand_id,
                    product_id,
                    country_code,
                    "price_snapshot_insert",
                    str(exc),
                    proxy_config=proxy_config,
                    listings=saved_listings + [listing],
                    price_snapshots=saved_snapshots,
                )

            saved_listings.append(listing)
            saved_snapshots.append(snapshot)

        return {
            "status": "ok",
            "brand_id": brand_id,
            "product_id": product_id,
            "country_code": country_code,
            "proxy_config": proxy_config,
            "listings": saved_listings,
            "price_snapshots": saved_snapshots,
        }
