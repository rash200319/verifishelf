import logging

from app.adapters.listing_adapter import crawl_listings, CrawlError
from app.core.proxy import get_proxy_config, ProxyConfigError
from app.repositories.brand_repository import BrandRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.listing_repository import ListingRepository
from app.repositories.price_snapshot_repository import PriceSnapshotRepository
from app.repositories.raw_crawl_result_repository import RawCrawlResultRepository
from app.schemas.crawl import CrawlListing, CrawlResult, NormalizedCrawlListing, NormalizedCrawlResult
from app.services.seller_fingerprint_service import SellerFingerprintService
from app.services.violation_service import ViolationService


logger = logging.getLogger(__name__)


def process_intelligence(brand_id: int, product_id: int, listings: list[dict]) -> None:
    """
    🔥 VIOLATION HOOK PLACEHOLDER (VERY IMPORTANT FOR TRACK B)
    
    This function is the critical integration point for Track B features:
    - ML inference for violation classification
    - Advanced seller fingerprinting and pattern detection
    - Feature extraction for analytics
    - Custom business logic per brand
    - Real-time alerting and notification triggers
    
    Currently empty (Track A scope), but structurally integrated into the crawl pipeline.
    Track B will implement the actual intelligence processing here.
    
    Args:
        brand_id: The brand ID
        product_id: The product ID
        listings: List of listing dictionaries that were just crawled
        
    Returns:
        None (side effects only - writes to database, triggers alerts, etc.)
    """
    # Track A: Empty placeholder
    # Track B will implement:
    # - ML model inference for violation severity classification
    # - Seller behavior pattern analysis
    # - Cross-marketplace price anomaly detection
    # - Automated alert generation
    # - Custom brand-specific rule evaluation
    pass


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
            seller_identity=str(listing["seller_identity"]).strip() if listing.get("seller_identity") else None,
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
            raw_data=result.get("raw_data"),
            listings=normalized_listings,
        )

    @staticmethod
    async def crawl_product(brand_id: int, product_id: int, country_code: str = "LK", crawl_job_id: int = 0):
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
            product = await ProductRepository.get_product_for_brand(product_id, brand_id)
            if product is None:
                return CrawlService._failure_result(
                    brand_id,
                    product_id,
                    country_code,
                    "product_lookup",
                    f"Product {product_id} not found",
                )
            product_name = product["name"]
            map_price = float(product["map_price"])
        except Exception as exc:
            logger.exception("Product lookup failed for brand_id=%s product_id=%s", brand_id, product_id)
            return CrawlService._failure_result(brand_id, product_id, country_code, "product_lookup", str(exc))

        try:
            proxy_config = get_proxy_config(country_code, brand["torch_sub_id"])
        except ProxyConfigError as exc:
            logger.warning(
                "No proxy pool configured for brand_id=%s product_id=%s country=%s",
                brand_id, product_id, country_code,
            )
            return CrawlService._failure_result(brand_id, product_id, country_code, "no_proxy_configured", str(exc))
        except Exception as exc:
            logger.exception("Proxy lookup failed for brand_id=%s product_id=%s", brand_id, product_id)
            return CrawlService._failure_result(brand_id, product_id, country_code, "proxy_lookup", str(exc))

        try:
            raw_result = await crawl_listings(brand_id, product_id, product_name, country_code, proxy_config)
        except CrawlError as exc:
            logger.exception("Adapter call failed for brand_id=%s product_id=%s", brand_id, product_id)
            return CrawlService._failure_result(
                brand_id,
                product_id,
                country_code,
                exc.step,
                str(exc),
                proxy_config=proxy_config,
            )
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

        if crawl_result.raw_data and crawl_job_id:
            try:
                await RawCrawlResultRepository.create_raw_result(
                    crawl_job_id,
                    brand_id,
                    product_id,
                    crawl_result.raw_data
                )
            except Exception as exc:
                logger.exception("Raw crawl result insert failed for brand_id=%s product_id=%s", brand_id, product_id)
                # Not failing the whole crawl if raw HTML save fails

        for crawl_listing in crawl_result.listings:
            try:
                seller = await SellerFingerprintService.resolve_seller(
                    crawl_listing.seller_name,
                    crawl_listing.seller_identity,
                    crawl_listing.listing_url,
                )
                resolved_seller_id = int(seller["id"])
            except Exception as exc:
                logger.exception("Seller fingerprint failed for brand_id=%s product_id=%s", brand_id, product_id)
                return CrawlService._failure_result(
                    brand_id,
                    product_id,
                    country_code,
                    "seller_fingerprint",
                    str(exc),
                    proxy_config=proxy_config,
                    listings=saved_listings,
                    price_snapshots=saved_snapshots,
                )

            try:
                existing_listing = await ListingRepository.find_listing(
                    crawl_listing.product_id,
                    resolved_seller_id,
                    crawl_listing.marketplace_id,
                )
                if existing_listing is None:
                    listing = await ListingRepository.create_listing(
                        crawl_listing.product_id,
                        resolved_seller_id,
                        crawl_listing.marketplace_id,
                        crawl_listing.listing_title,
                        crawl_listing.listing_url,
                        crawl_listing.image_url,
                        crawl_listing.advertised_price,
                        crawl_listing.currency_code,
                    )
                else:
                    listing = await ListingRepository.update_listing(
                        existing_listing["id"],
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
                    resolved_seller_id,
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

            try:
                await ViolationService.evaluate_listing_price(
                    brand_id=brand_id,
                    product_id=product_id,
                    listing_id=listing["id"],
                    map_price=map_price,
                    advertised_price=crawl_listing.advertised_price,
                    marketplace_id=crawl_listing.marketplace_id,
                    listing_title=crawl_listing.listing_title,
                    product_name=product_name,
                    seller_id=resolved_seller_id,
                )
            except Exception as exc:
                logger.exception("Violation detection failed for listing %s", listing["id"])

            saved_listings.append(listing)
            saved_snapshots.append(snapshot)

        # 🔥 IMPORTANT HOOK (Track B attaches here)
        # This hook is the integration point for:
        # - ML inference and violation classification
        # - Seller fingerprinting and pattern detection
        # - Advanced analytics and feature extraction
        # - Custom business logic per brand
        process_intelligence(brand_id, product_id, saved_listings)

        return {
            "status": "ok",
            "brand_id": brand_id,
            "product_id": product_id,
            "country_code": country_code,
            "proxy_config": proxy_config,
            "listings": saved_listings,
            "price_snapshots": saved_snapshots,
        }
