from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import AsyncMock, patch

from app.services.violation_service import ViolationService


class ViolationServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_creates_violation_when_below_map_and_no_promo(self):
        with patch("app.services.violation_service.PromoService.is_below_map_allowed", AsyncMock(return_value=False)), \
            patch("app.services.violation_service.ViolationRepository.get_open_violation_for_listing", AsyncMock(return_value=None)), \
            patch("app.services.violation_service.ViolationRepository.create_violation", AsyncMock(return_value={"id": 9, "price_delta_pct": 15.0})) as create_mock:
            result = await ViolationService.evaluate_listing_price(
                brand_id=1,
                product_id=1,
                listing_id=10,
                map_price=25000,
                advertised_price=21000,
                marketplace_id=1,
            )

        self.assertEqual(result["action"], "created")
        self.assertEqual(result["severity"], "medium")
        create_mock.assert_awaited_once()

    async def test_suppresses_violation_when_promo_window_active(self):
        with patch("app.services.violation_service.PromoService.is_below_map_allowed", AsyncMock(return_value=True)), \
            patch("app.services.violation_service.ViolationRepository.get_open_violation_for_listing", AsyncMock(return_value=None)), \
            patch("app.services.violation_service.ViolationRepository.create_violation", AsyncMock()) as create_mock:
            result = await ViolationService.evaluate_listing_price(
                brand_id=1,
                product_id=1,
                listing_id=10,
                map_price=25000,
                advertised_price=21000,
                marketplace_id=1,
                check_date=date(2026, 6, 15),
            )

        self.assertEqual(result["action"], "suppressed")
        create_mock.assert_not_awaited()

    async def test_resolves_existing_violation_when_price_returns_to_map(self):
        existing = {"id": 4, "price_delta_pct": 12.0}
        with patch("app.services.violation_service.ViolationRepository.get_open_violation_for_listing", AsyncMock(return_value=existing)), \
            patch("app.services.violation_service.ViolationRepository.update_violation_status", AsyncMock()) as update_mock:
            result = await ViolationService.evaluate_listing_price(
                brand_id=1,
                product_id=1,
                listing_id=10,
                map_price=25000,
                advertised_price=25000,
                marketplace_id=1,
            )

        self.assertEqual(result["action"], "resolved")
        update_mock.assert_awaited_once_with(4, "resolved")

    def test_compute_severity_buckets(self):
        self.assertEqual(ViolationService.compute_severity(25), "high")
        self.assertEqual(ViolationService.compute_severity(12), "medium")
        self.assertEqual(ViolationService.compute_severity(5), "low")
