from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import AsyncMock, patch

from app.services.promo_service import PromoService


class PromoServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_create_promo_requires_product_in_brand(self):
        with patch("app.services.promo_service.ProductRepository.get_product_for_brand", AsyncMock(return_value=None)):
            with self.assertRaises(ValueError):
                await PromoService.create_promo(1, 99, 1, date(2026, 6, 1), date(2026, 6, 7), "launch promo")

    async def test_create_promo_persists_window(self):
        product = {"id": 1, "brand_id": 1, "name": "Demo Product", "map_price": 25000}
        promo_row = {
            "id": 10,
            "brand_id": 1,
            "product_id": 1,
            "marketplace_id": 1,
            "start_date": date(2026, 6, 1),
            "end_date": date(2026, 6, 7),
            "notes": "launch promo",
            "created_at": "2026-06-15 00:00:00",
        }

        with patch("app.services.promo_service.ProductRepository.get_product_for_brand", AsyncMock(return_value=product)), \
            patch("app.services.promo_service.PromoRepository.create_promo", AsyncMock(return_value=promo_row)) as create_mock:
            result = await PromoService.create_promo(1, 1, 1, date(2026, 6, 1), date(2026, 6, 7), "launch promo")

        self.assertEqual(result["id"], 10)
        create_mock.assert_awaited_once_with(1, 1, 1, date(2026, 6, 1), date(2026, 6, 7), "launch promo")

    async def test_is_below_map_allowed_delegates_to_repository(self):
        with patch("app.services.promo_service.PromoRepository.has_active_promo", AsyncMock(return_value=True)) as promo_mock:
            allowed = await PromoService.is_below_map_allowed(1, 1, 1, date(2026, 6, 5))

        self.assertTrue(allowed)
        promo_mock.assert_awaited_once_with(1, 1, 1, date(2026, 6, 5))
