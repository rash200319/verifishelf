from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import AsyncMock, patch

from app.services.weekly_report_service import WeeklyReportService


class WeeklyReportServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_generate_report_builds_narrative_and_stores_payload(self):
        brand = {"id": 1, "name": "Demo Brand"}
        metrics = {
            "summary": {
                "listings_monitored": 2,
                "price_snapshots": 5,
                "violations_detected": 1,
                "violations_open": 1,
                "active_promo_windows": 1,
            },
            "products": [
                {
                    "product_id": 1,
                    "product_name": "Demo Product",
                    "map_price": 25000,
                    "avg_observed_price": 21058,
                    "snapshot_count": 5,
                    "latest_price": 21058,
                }
            ],
        }
        stored_row = {
            "id": 3,
            "brand_id": 1,
            "report_start_date": date(2026, 6, 9),
            "report_end_date": date(2026, 6, 15),
            "report_content": '{"summary": {}, "products": [], "narrative": "placeholder"}',
            "generated_at": "2026-06-15 12:00:00",
        }

        async def fake_create_report(brand_id, start_date, end_date, payload):
            stored_row["report_content"] = __import__("json").dumps(payload, default=str)
            return stored_row

        with patch("app.services.weekly_report_service.BrandRepository.get_brand_by_id", AsyncMock(return_value=brand)), \
            patch("app.services.weekly_report_service.WeeklyReportRepository.aggregate_brand_metrics", AsyncMock(return_value=metrics)), \
            patch("app.services.weekly_report_service.WeeklyReportRepository.create_report", AsyncMock(side_effect=fake_create_report)):
            report = await WeeklyReportService.generate_report(1, date(2026, 6, 9), date(2026, 6, 15))

        self.assertEqual(report["id"], 3)
        self.assertEqual(report["summary"]["price_snapshots"], 5)
        self.assertIn("Demo Brand", report["narrative"])
        self.assertEqual(len(report["products"]), 1)

    async def test_generate_report_rejects_invalid_range(self):
        with self.assertRaises(ValueError):
            await WeeklyReportService.generate_report(1, date(2026, 6, 15), date(2026, 6, 1))
