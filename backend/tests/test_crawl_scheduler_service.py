from __future__ import annotations

import unittest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

from app.services.crawl_scheduler_service import CrawlSchedulerService


class CrawlSchedulerServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_is_brand_due_when_no_previous_job(self):
        with patch("app.services.crawl_scheduler_service.CrawlJobRepository.get_latest_job", AsyncMock(return_value=None)):
            due = await CrawlSchedulerService.is_brand_due(1, "starter", 1)

        self.assertTrue(due)

    async def test_is_brand_not_due_when_job_running(self):
        latest_job = {
            "id": 1,
            "brand_id": 1,
            "marketplace_id": 1,
            "status": "running",
            "started_at": datetime.now(),
            "finished_at": None,
            "created_at": datetime.now(),
        }

        with patch("app.services.crawl_scheduler_service.CrawlJobRepository.get_latest_job", AsyncMock(return_value=latest_job)):
            due = await CrawlSchedulerService.is_brand_due(1, "starter", 1)

        self.assertFalse(due)

    async def test_dispatch_enqueues_only_due_brands(self):
        enabled_bms = [
            {
                "brand_marketplace_id": 1,
                "brand_id": 1,
                "marketplace_id": 1,
                "brand_name": "Demo Brand",
                "brand_plan": "starter",
                "marketplace_name": "Daraz",
                "marketplace_country_code": "LK",
                "country_code": "LK",
                "crawl_frequency_hrs": None,
                "enabled": True,
                "priority": 1,
            }
        ]

        with patch("app.services.crawl_scheduler_service.CrawlSchedulerService._load_enabled_brand_marketplaces", AsyncMock(return_value=enabled_bms)), \
            patch("app.services.crawl_scheduler_service.CrawlSchedulerService.is_brand_due", AsyncMock(return_value=True)), \
            patch("app.services.crawl_scheduler_service.CrawlJobRepository.create_job", AsyncMock(return_value={"id": 9, "brand_id": 1, "marketplace_id": 1, "status": "queued", "started_at": None, "finished_at": None, "created_at": datetime.now()})):
            result = await CrawlSchedulerService.dispatch_due_crawls("LK")

        self.assertEqual(len(result["dispatched"]), 1)
        self.assertEqual(result["dispatched"][0]["crawl_job_id"], 9)
        self.assertEqual(result["dispatched"][0]["interval_seconds"], 120)

    async def test_run_brand_crawl_marks_job_completed(self):
        products = [{"id": 1, "brand_id": 1, "name": "Demo Product"}]
        crawl_result = {"status": "ok", "listings": [], "price_snapshots": []}

        update_mock = AsyncMock(side_effect=[
            {"id": 5, "status": "running"},
            {"id": 5, "status": "completed"},
        ])

        with patch("app.services.crawl_scheduler_service.CrawlJobRepository.update_job_status", update_mock), \
            patch("app.services.crawl_scheduler_service.ProductRepository.list_products_for_brand", AsyncMock(return_value=products)), \
            patch("app.services.crawl_service.CrawlService.crawl_product", AsyncMock(return_value=crawl_result)):
            result = await CrawlSchedulerService.run_brand_crawl(5, 1, "LK")

        self.assertEqual(result["status"], "completed")
        self.assertEqual(update_mock.await_count, 2)

    async def test_run_brand_crawl_marks_job_failed_without_products(self):
        update_mock = AsyncMock(return_value={"id": 6, "status": "failed"})

        with patch("app.services.crawl_scheduler_service.CrawlJobRepository.update_job_status", update_mock), \
            patch("app.services.crawl_scheduler_service.ProductRepository.list_products_for_brand", AsyncMock(return_value=[])):
            result = await CrawlSchedulerService.run_brand_crawl(6, 1, "LK")

        self.assertEqual(result["status"], "failed")
        update_mock.assert_awaited()
