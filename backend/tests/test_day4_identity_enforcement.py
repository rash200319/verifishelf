from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from app.services.enforcement_service import EnforcementService
from app.services.seller_fingerprint_service import SellerFingerprintService, compute_seller_signature


class SellerFingerprintServiceTestCase(unittest.IsolatedAsyncioTestCase):
    def test_compute_seller_signature_is_stable(self):
        signature = compute_seller_signature("Daraz Seller", "daraz-seller-1", "https://www.daraz.lk/shop/demo-seller")
        self.assertEqual(signature["normalized_name"], "darazseller")
        self.assertEqual(len(signature["signature_hash"]), 16)

    async def test_resolve_seller_reuses_existing_signature(self):
        existing = {"id": 3, "cluster_id": 1, "seller_name": "Daraz Seller", "embedding": {"signature_hash": "abc"}}
        with patch("app.services.seller_fingerprint_service.SellerRepository.find_by_signature_hash", AsyncMock(return_value=existing)):
            seller = await SellerFingerprintService.resolve_seller("Daraz Seller", "daraz-seller-1", "https://example.com")

        self.assertEqual(seller["id"], 3)

    async def test_resolve_seller_links_similar_names_to_cluster(self):
        similar = {"id": 2, "cluster_id": 5, "seller_name": "DarazSeller", "embedding": {"normalized_name": "darazseller"}}
        created = {"id": 6, "cluster_id": 5, "seller_name": "Daraz Seller Official"}

        with patch("app.services.seller_fingerprint_service.SellerRepository.find_by_signature_hash", AsyncMock(return_value=None)), \
            patch("app.services.seller_fingerprint_service.SellerRepository.find_by_normalized_name", AsyncMock(return_value=similar)), \
            patch("app.services.seller_fingerprint_service.SellerRepository.create_seller", AsyncMock(return_value=created)) as create_mock:
            seller = await SellerFingerprintService.resolve_seller(
                "Daraz Seller Official",
                "daraz-seller-official",
                "https://www.daraz.lk/shop/daraz-seller-official",
            )

        self.assertEqual(seller["id"], 6)
        create_mock.assert_awaited_once()


class EnforcementServiceTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_generate_for_violation_uses_template(self):
        context = {
            "violation_id": 1,
            "map_price": 25000,
            "advertised_price": 21000,
            "price_delta_pct": 16,
            "status": "open",
            "detected_at": "2026-06-15 10:00:00",
            "listing_title": "Demo Listing",
            "listing_url": "https://example.com/listing",
            "currency_code": "LKR",
            "product_name": "Demo Product",
            "brand_name": "Demo Brand",
            "seller_name": "Daraz Seller",
            "storefront_url": "https://example.com/shop",
        }
        stored = {
            "id": 1,
            "violation_id": 1,
            "letter_content": "Subject: MAP Violation Notice",
            "generated_by": "template",
            "generated_at": "2026-06-15 10:05:00",
        }

        with patch("app.services.enforcement_service.EnforcementLetterRepository.get_latest_for_violation", AsyncMock(return_value=None)), \
            patch("app.services.enforcement_service.EnforcementLetterRepository.get_violation_context", AsyncMock(return_value=context)), \
            patch("app.services.enforcement_service.EnforcementLetterRepository.create_letter", AsyncMock(return_value=stored)) as create_mock:
            letter = await EnforcementService.generate_for_violation(1, 1)

        self.assertEqual(letter["generated_by"], "template")
        create_mock.assert_awaited_once()

    def test_build_template_letter_includes_violation_context(self):
        letter = EnforcementService.build_template_letter(
            {
                "product_name": "Demo Product",
                "seller_name": "Daraz Seller",
                "listing_title": "Demo Listing",
                "listing_url": "https://example.com/listing",
                "map_price": 25000,
                "advertised_price": 21000,
                "price_delta_pct": 16,
                "currency_code": "LKR",
                "detected_at": "2026-06-15 10:00:00",
                "status": "open",
                "brand_name": "Demo Brand",
            }
        )

        self.assertIn("MAP Violation Notice", letter)
        self.assertIn("Daraz Seller", letter)
        self.assertIn("Demo Brand", letter)
