from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, Mock, patch

from app.schemas.crawl import CrawlListing, CrawlResult
from app.services.crawl_service import CrawlService


class CrawlServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_crawl_product_writes_listing_then_snapshot_and_uses_proxy(self):
        brand = {"id": 7, "torch_sub_id": "torch_brand_7"}
        raw_result = CrawlResult(
            brand_id=7,
            product_id=11,
            country_code="LK",
            proxy_config={"host": "proxy.local", "port": 8080},
            listings=[
                CrawlListing(
                    product_id=11,
                    seller_id=21,
                    marketplace_id=31,
                    seller_name="Sample Seller",
                    listing_title="Sample Listing",
                    listing_url="https://example.com/listings/sample",
                    image_url="https://example.com/images/sample.jpg",
                    advertised_price=123.45,
                    currency_code="usd",
                )
            ],
        )

        listing_row = {
            "id": 101,
            "product_id": 11,
            "seller_id": 21,
            "marketplace_id": 31,
            "listing_title": "Sample Listing",
            "listing_url": "https://example.com/listings/sample",
            "image_url": "https://example.com/images/sample.jpg",
            "advertised_price": 123.45,
            "currency_code": "USD",
            "scraped_at": "2026-06-15 00:00:00",
        }
        snapshot_row = {
            "id": 202,
            "listing_id": 101,
            "product_id": 11,
            "seller_id": 21,
            "price": 123.45,
            "snapshot_time": "2026-06-15 00:00:01",
        }

        proxy_calls: list[tuple[str, str]] = []

        def fake_proxy_lookup(country_code: str, brand_sub_id: str):
            proxy_calls.append((country_code, brand_sub_id))
            return {"host": "proxy.local", "port": 8080}

        listing_repo = Mock()
        listing_repo.find_listing = AsyncMock(return_value=None)
        listing_repo.create_listing = AsyncMock(return_value=listing_row)
        snapshot_repo = Mock()
        snapshot_repo.create_price_snapshot = AsyncMock(return_value=snapshot_row)
        brand_repo = Mock()
        brand_repo.get_brand_by_id = AsyncMock(return_value=brand)
        product_repo = Mock()
        product_repo.get_product_for_brand = AsyncMock(return_value={"name": "Sample Product", "map_price": 100.0})
        raw_result_repo = Mock()
        raw_result_repo.create_raw_result = AsyncMock()
        seller_fingerprint = Mock()
        seller_fingerprint.resolve_seller = AsyncMock(return_value={"id": 21, "cluster_id": 1})
        violation_service = Mock()
        violation_service.evaluate_listing_price = AsyncMock(return_value={"action": "none"})

        with patch("app.services.crawl_service.BrandRepository", brand_repo), \
            patch("app.services.crawl_service.ProductRepository", product_repo), \
            patch("app.services.crawl_service.get_proxy_config", side_effect=fake_proxy_lookup), \
            patch("app.services.crawl_service.crawl_listings", AsyncMock(return_value=raw_result)), \
            patch("app.services.crawl_service.ListingRepository", listing_repo), \
            patch("app.services.crawl_service.RawCrawlResultRepository", raw_result_repo), \
            patch("app.services.crawl_service.SellerFingerprintService", seller_fingerprint), \
            patch("app.services.crawl_service.ViolationService", violation_service), \
            patch("app.services.crawl_service.PriceSnapshotRepository", snapshot_repo):
            result = await CrawlService.crawl_product(brand_id=7, product_id=11, country_code="LK")

        self.assertEqual(proxy_calls, [("LK", "torch_brand_7")])
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["listings"]), 1)
        self.assertEqual(len(result["price_snapshots"]), 1)
        listing_repo.create_listing.assert_awaited_once_with(
            11,
            21,
            31,
            "Sample Listing",
            "https://example.com/listings/sample",
            "https://example.com/images/sample.jpg",
            123.45,
            "USD",
        )
        snapshot_repo.create_price_snapshot.assert_awaited_once_with(101, 11, 21, 123.45)

    async def test_listing_insert_failure_stops_before_snapshot(self):
        brand = {"id": 7, "torch_sub_id": "torch_brand_7"}
        raw_result = CrawlResult(
            brand_id=7,
            product_id=11,
            country_code="LK",
            proxy_config=None,
            listings=[
                CrawlListing(
                    product_id=11,
                    seller_id=21,
                    marketplace_id=31,
                    seller_name="Sample Seller",
                    listing_title="Sample Listing",
                    listing_url="https://example.com/listings/sample",
                    image_url=None,
                    advertised_price=123.45,
                    currency_code="USD",
                )
            ],
        )

        brand_repo = Mock()
        brand_repo.get_brand_by_id = AsyncMock(return_value=brand)
        product_repo = Mock()
        product_repo.get_product_for_brand = AsyncMock(return_value={"name": "Sample Product", "map_price": 100.0})

        listing_repo = Mock()
        listing_repo.find_listing = AsyncMock(return_value=None)
        listing_repo.create_listing = AsyncMock(side_effect=RuntimeError("insert failed"))
        snapshot_repo = Mock()
        snapshot_repo.create_price_snapshot = AsyncMock()
        raw_result_repo = Mock()
        raw_result_repo.create_raw_result = AsyncMock()
        seller_fingerprint = Mock()
        seller_fingerprint.resolve_seller = AsyncMock(return_value={"id": 21})
        violation_service = Mock()

        with patch("app.services.crawl_service.BrandRepository", brand_repo), \
            patch("app.services.crawl_service.ProductRepository", product_repo), \
            patch("app.services.crawl_service.get_proxy_config", return_value=None) as proxy_mock, \
            patch("app.services.crawl_service.crawl_listings", AsyncMock(return_value=raw_result)), \
            patch("app.services.crawl_service.ListingRepository", listing_repo), \
            patch("app.services.crawl_service.RawCrawlResultRepository", raw_result_repo), \
            patch("app.services.crawl_service.SellerFingerprintService", seller_fingerprint), \
            patch("app.services.crawl_service.ViolationService", violation_service), \
            patch("app.services.crawl_service.PriceSnapshotRepository", snapshot_repo):
            result = await CrawlService.crawl_product(brand_id=7, product_id=11, country_code="LK")

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["failed_step"], "listing_insert")
        proxy_mock.assert_called_once_with("LK", "torch_brand_7")
        snapshot_repo.create_price_snapshot.assert_not_awaited()

    async def test_crawl_product_updates_existing_listing_before_snapshot(self):
        brand = {"id": 7, "torch_sub_id": "torch_brand_7"}
        raw_result = CrawlResult(
            brand_id=7,
            product_id=11,
            country_code="LK",
            proxy_config=None,
            listings=[
                CrawlListing(
                    product_id=11,
                    seller_id=21,
                    marketplace_id=31,
                    seller_name="Sample Seller",
                    listing_title="Updated Listing",
                    listing_url="https://example.com/listings/sample",
                    image_url=None,
                    advertised_price=99.99,
                    currency_code="LKR",
                )
            ],
        )

        existing_listing = {
            "id": 101,
            "product_id": 11,
            "seller_id": 21,
            "marketplace_id": 31,
            "listing_title": "Old Listing",
            "listing_url": "https://example.com/listings/sample",
            "image_url": None,
            "advertised_price": 123.45,
            "currency_code": "USD",
            "scraped_at": "2026-06-15 00:00:00",
        }
        updated_listing = {**existing_listing, "advertised_price": 99.99, "currency_code": "LKR"}
        snapshot_row = {
            "id": 303,
            "listing_id": 101,
            "product_id": 11,
            "seller_id": 21,
            "price": 99.99,
            "snapshot_time": "2026-06-15 00:00:02",
        }

        brand_repo = Mock()
        brand_repo.get_brand_by_id = AsyncMock(return_value=brand)
        product_repo = Mock()
        product_repo.get_product_for_brand = AsyncMock(return_value={"name": "Sample Product", "map_price": 100.0})
        listing_repo = Mock()
        listing_repo.find_listing = AsyncMock(return_value=existing_listing)
        listing_repo.update_listing = AsyncMock(return_value=updated_listing)
        listing_repo.create_listing = AsyncMock()
        snapshot_repo = Mock()
        snapshot_repo.create_price_snapshot = AsyncMock(return_value=snapshot_row)
        raw_result_repo = Mock()
        raw_result_repo.create_raw_result = AsyncMock()
        seller_fingerprint = Mock()
        seller_fingerprint.resolve_seller = AsyncMock(return_value={"id": 21})
        violation_service = Mock()
        violation_service.evaluate_listing_price = AsyncMock(return_value={"action": "none"})

        with patch("app.services.crawl_service.BrandRepository", brand_repo), \
            patch("app.services.crawl_service.ProductRepository", product_repo), \
            patch("app.services.crawl_service.get_proxy_config", return_value=None), \
            patch("app.services.crawl_service.crawl_listings", AsyncMock(return_value=raw_result)), \
            patch("app.services.crawl_service.ListingRepository", listing_repo), \
            patch("app.services.crawl_service.RawCrawlResultRepository", raw_result_repo), \
            patch("app.services.crawl_service.SellerFingerprintService", seller_fingerprint), \
            patch("app.services.crawl_service.ViolationService", violation_service), \
            patch("app.services.crawl_service.PriceSnapshotRepository", snapshot_repo):
            result = await CrawlService.crawl_product(brand_id=7, product_id=11, country_code="LK")

        self.assertEqual(result["status"], "ok")
        listing_repo.create_listing.assert_not_awaited()
        listing_repo.update_listing.assert_awaited_once()
        snapshot_repo.create_price_snapshot.assert_awaited_once_with(101, 11, 21, 99.99)
