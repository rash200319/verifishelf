from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import AsyncMock, patch

from app.services.violation_service import ViolationService


class ViolationServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_creates_violation_when_below_map_and_no_promo(self):
        with patch("app.services.violation_service.PromoService.is_below_map_allowed", AsyncMock(return_value=False)), \
            patch("app.services.violation_service.ViolationRepository.get_open_violation_for_listing", AsyncMock(return_value=None)), \
            patch("app.services.violation_service.ViolationRepository.get_recently_resolved_violation", AsyncMock(return_value=None)), \
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

    async def test_does_not_resolve_on_a_single_compliant_check(self):
        existing = {"id": 4, "price_delta_pct": 12.0}
        with patch("app.services.violation_service.ViolationRepository.get_open_violation_for_listing", AsyncMock(return_value=existing)), \
            patch("app.services.violation_service.ViolationRepository.bump_compliant_streak", AsyncMock(return_value=1)) as bump_mock, \
            patch("app.services.violation_service.ViolationRepository.resolve_violation", AsyncMock()) as resolve_mock:
            result = await ViolationService.evaluate_listing_price(
                brand_id=1,
                product_id=1,
                listing_id=10,
                map_price=25000,
                advertised_price=25000,
                marketplace_id=1,
            )

        self.assertEqual(result["action"], "pending_resolution")
        bump_mock.assert_awaited_once_with(4)
        resolve_mock.assert_not_awaited()

    async def test_resolves_existing_violation_after_sustained_compliance(self):
        existing = {"id": 4, "price_delta_pct": 12.0}
        with patch("app.services.violation_service.ViolationRepository.get_open_violation_for_listing", AsyncMock(return_value=existing)), \
            patch("app.services.violation_service.ViolationRepository.bump_compliant_streak", AsyncMock(return_value=2)), \
            patch("app.services.violation_service.ViolationRepository.resolve_violation", AsyncMock()) as resolve_mock:
            result = await ViolationService.evaluate_listing_price(
                brand_id=1,
                product_id=1,
                listing_id=10,
                map_price=25000,
                advertised_price=25000,
                marketplace_id=1,
            )

        self.assertEqual(result["action"], "resolved")
        resolve_mock.assert_awaited_once_with(4)

    async def test_resets_streak_when_violation_recurs_before_resolving(self):
        existing = {"id": 4, "price_delta_pct": 12.0}
        with patch("app.services.violation_service.PromoService.is_below_map_allowed", AsyncMock(return_value=False)), \
            patch("app.services.violation_service.ViolationRepository.get_open_violation_for_listing", AsyncMock(return_value=existing)), \
            patch("app.services.violation_service.ViolationRepository.reset_compliant_streak", AsyncMock()) as reset_mock:
            result = await ViolationService.evaluate_listing_price(
                brand_id=1,
                product_id=1,
                listing_id=10,
                map_price=25000,
                advertised_price=21000,
                marketplace_id=1,
            )

        self.assertEqual(result["action"], "existing")
        reset_mock.assert_awaited_once_with(4)

    async def test_reopens_recently_resolved_violation_instead_of_creating_new_row(self):
        recent = {"id": 7}
        with patch("app.services.violation_service.PromoService.is_below_map_allowed", AsyncMock(return_value=False)), \
            patch("app.services.violation_service.ViolationRepository.get_open_violation_for_listing", AsyncMock(return_value=None)), \
            patch("app.services.violation_service.ViolationRepository.get_recently_resolved_violation", AsyncMock(return_value=recent)) as recent_mock, \
            patch("app.services.violation_service.ViolationRepository.reopen_violation", AsyncMock(return_value={"id": 7, "price_delta_pct": 15.0})) as reopen_mock, \
            patch("app.services.violation_service.ViolationRepository.create_violation", AsyncMock()) as create_mock:
            result = await ViolationService.evaluate_listing_price(
                brand_id=1,
                product_id=1,
                listing_id=10,
                map_price=25000,
                advertised_price=21000,
                marketplace_id=1,
            )

        self.assertEqual(result["action"], "reopened")
        self.assertEqual(result["violation_id"], 7)
        recent_mock.assert_awaited_once_with(10, within_days=ViolationService.REOPEN_WINDOW_DAYS)
        reopen_mock.assert_awaited_once()
        create_mock.assert_not_awaited()

    def test_compute_severity_buckets(self):
        self.assertEqual(ViolationService.compute_severity(25), "high")
        self.assertEqual(ViolationService.compute_severity(12), "medium")
        self.assertEqual(ViolationService.compute_severity(5), "low")

    async def test_creates_violation_uses_real_classifier_when_seller_context_provided(self):
        seller = {"id": 42, "seller_name": "Some Seller", "created_at": "2026-01-01 00:00:00"}
        with patch("app.services.violation_service.PromoService.is_below_map_allowed", AsyncMock(return_value=False)), \
            patch("app.services.violation_service.ViolationRepository.get_open_violation_for_listing", AsyncMock(return_value=None)), \
            patch("app.services.violation_service.ViolationRepository.get_recently_resolved_violation", AsyncMock(return_value=None)), \
            patch("app.services.violation_service.SellerRepository.get_seller_by_id", AsyncMock(return_value=seller)) as seller_mock, \
            patch("app.services.violation_service.ViolationRepository.count_violations_for_seller", AsyncMock(return_value=3)) as count_mock, \
            patch("app.services.violation_service.ViolationRepository.create_violation", AsyncMock(return_value={"id": 9, "price_delta_pct": 15.0})) as create_mock:
            result = await ViolationService.evaluate_listing_price(
                brand_id=1,
                product_id=1,
                listing_id=10,
                map_price=25000,
                advertised_price=21000,
                marketplace_id=1,
                listing_title="Some Product - Reseller Listing",
                product_name="Some Product",
                seller_id=42,
            )

        self.assertEqual(result["action"], "created")
        seller_mock.assert_awaited_once_with(42)
        count_mock.assert_awaited_once_with(42)
        create_mock.assert_awaited_once()
        _, kwargs = create_mock.call_args
        self.assertIn(kwargs["classifier_type"], {"xgboost_v1", "heuristic"})
        self.assertIsInstance(kwargs["classifier_confidence"], float)

    async def test_creates_violation_falls_back_to_heuristic_without_seller_id(self):
        with patch("app.services.violation_service.PromoService.is_below_map_allowed", AsyncMock(return_value=False)), \
            patch("app.services.violation_service.ViolationRepository.get_open_violation_for_listing", AsyncMock(return_value=None)), \
            patch("app.services.violation_service.ViolationRepository.get_recently_resolved_violation", AsyncMock(return_value=None)), \
            patch("app.services.violation_service.ViolationRepository.create_violation", AsyncMock(return_value={"id": 9, "price_delta_pct": 15.0})) as create_mock:
            await ViolationService.evaluate_listing_price(
                brand_id=1,
                product_id=1,
                listing_id=10,
                map_price=25000,
                advertised_price=21000,
                marketplace_id=1,
            )

        _, kwargs = create_mock.call_args
        self.assertEqual(kwargs["classifier_confidence"], 0.99)
        self.assertEqual(kwargs["classifier_type"], "heuristic")
