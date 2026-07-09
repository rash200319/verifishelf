from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from app.core.auth import create_access_token, require_superadmin
from app.services.auth_service import AuthService
from app.services.brand_service import BrandService


class AuthAndAdminTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_get_registration_status_user_not_found(self):
        with patch("app.services.auth_service.UserRepository.get_user_by_email", AsyncMock(return_value=None)):
            status = await AuthService.get_registration_status("missing@example.com")
            self.assertIsNone(status)

    async def test_get_registration_status_brand_not_found(self):
        user = {"id": 1, "brand_id": 99, "email": "test@example.com"}
        with patch("app.services.auth_service.UserRepository.get_user_by_email", AsyncMock(return_value=user)), \
             patch("app.services.auth_service.BrandRepository.get_brand_by_id", AsyncMock(return_value=None)):
            status = await AuthService.get_registration_status("test@example.com")
            self.assertIsNone(status)

    async def test_get_registration_status_success(self):
        user = {"id": 1, "brand_id": 2, "email": "test@example.com"}
        brand = {"id": 2, "name": "Acme Brand", "status": "pending_review"}
        with patch("app.services.auth_service.UserRepository.get_user_by_email", AsyncMock(return_value=user)), \
             patch("app.services.auth_service.BrandRepository.get_brand_by_id", AsyncMock(return_value=brand)):
            status = await AuthService.get_registration_status("test@example.com")
            self.assertIsNotNone(status)
            self.assertEqual(status["brand_name"], "Acme Brand")
            self.assertEqual(status["status"], "pending_review")

    async def test_login_allows_pending_review_brand_to_complete_onboarding(self):
        # Deliberate, documented behavior (see AuthService.login): a brand
        # admin must be able to log in while their brand is still
        # pending_review to finish onboarding after payment. This was
        # previously (mis-)tested as a rejection case under the name
        # test_login_requires_approved_brand -- pending_review was never
        # actually supposed to be rejected, only rejected/needs_more_info are.
        user = {
            "id": 1,
            "brand_id": 2,
            "email": "test@example.com",
            "password_hash": "hashed",
            "is_active": True
        }
        brand = {"id": 2, "name": "Acme Brand", "status": "pending_review"}

        with patch("app.services.auth_service.UserRepository.get_user_by_email", AsyncMock(return_value=user)), \
             patch("app.services.auth_service.verify_password", return_value=True), \
             patch("app.services.auth_service.BrandRepository.get_brand_by_id", AsyncMock(return_value=brand)):
            session = await AuthService.login("test@example.com", "password")
            self.assertIsNotNone(session)
            self.assertEqual(session["brand"]["status"], "pending_review")

    async def test_login_rejects_rejected_brand(self):
        user = {
            "id": 1,
            "brand_id": 2,
            "email": "test@example.com",
            "password_hash": "hashed",
            "is_active": True
        }
        brand = {"id": 2, "name": "Acme Brand", "status": "rejected"}

        with patch("app.services.auth_service.UserRepository.get_user_by_email", AsyncMock(return_value=user)), \
             patch("app.services.auth_service.verify_password", return_value=True), \
             patch("app.services.auth_service.BrandRepository.get_brand_by_id", AsyncMock(return_value=brand)):
            session = await AuthService.login("test@example.com", "password")
            self.assertIsNone(session)

    async def test_login_rejects_needs_more_info_brand(self):
        user = {
            "id": 1,
            "brand_id": 2,
            "email": "test@example.com",
            "password_hash": "hashed",
            "is_active": True
        }
        brand = {"id": 2, "name": "Acme Brand", "status": "needs_more_info"}

        with patch("app.services.auth_service.UserRepository.get_user_by_email", AsyncMock(return_value=user)), \
             patch("app.services.auth_service.verify_password", return_value=True), \
             patch("app.services.auth_service.BrandRepository.get_brand_by_id", AsyncMock(return_value=brand)):
            session = await AuthService.login("test@example.com", "password")
            self.assertIsNone(session)

    async def test_login_allows_superadmin_with_no_brand(self):
        user = {
            "id": 1,
            "brand_id": None,
            "email": "superadmin@example.com",
            "password_hash": "hashed",
            "role": "superadmin",
            "is_active": True,
        }

        with patch("app.services.auth_service.UserRepository.get_user_by_email", AsyncMock(return_value=user)), \
             patch("app.services.auth_service.verify_password", return_value=True), \
             patch("app.services.auth_service.BrandRepository.get_brand_by_id", AsyncMock()) as brand_lookup:
            session = await AuthService.login("superadmin@example.com", "password")
            self.assertIsNotNone(session)
            self.assertIsNone(session["brand"])
            brand_lookup.assert_not_awaited()

    async def test_login_rejects_null_brand_non_superadmin(self):
        # Defensive case -- brand_id should only ever be NULL for a
        # superadmin row, but if it somehow isn't, login must not silently
        # succeed with no brand context.
        user = {
            "id": 1,
            "brand_id": None,
            "email": "test@example.com",
            "password_hash": "hashed",
            "role": "admin",
            "is_active": True,
        }

        with patch("app.services.auth_service.UserRepository.get_user_by_email", AsyncMock(return_value=user)), \
             patch("app.services.auth_service.verify_password", return_value=True):
            session = await AuthService.login("test@example.com", "password")
            self.assertIsNone(session)

    async def test_login_requires_active_user(self):
        user = {
            "id": 1,
            "brand_id": 2,
            "email": "test@example.com",
            "password_hash": "hashed",
            "is_active": False
        }
        brand = {"id": 2, "name": "Acme Brand", "status": "approved"}

        with patch("app.services.auth_service.UserRepository.get_user_by_email", AsyncMock(return_value=user)), \
             patch("app.services.auth_service.verify_password", return_value=True), \
             patch("app.services.auth_service.BrandRepository.get_brand_by_id", AsyncMock(return_value=brand)):
            session = await AuthService.login("test@example.com", "password")
            self.assertIsNone(session)

    async def test_approve_brand_updates_and_activates_owner(self):
        brand = {"id": 2, "name": "Acme Brand", "status": "approved"}
        update_mock = AsyncMock(return_value=brand)
        activate_mock = AsyncMock()

        with patch("app.services.brand_service.BrandRepository.update_brand_review", update_mock), \
             patch("app.services.brand_service.UserRepository.activate_brand_owner_users", activate_mock):
            result = await BrandService.approve_brand(2, reviewed_by="admin_user", review_notes="looks good")
            self.assertEqual(result, brand)
            update_mock.assert_awaited_once_with(2, status="approved", reviewed_by="admin_user", review_notes="looks good")
            activate_mock.assert_awaited_once_with(2)

    async def test_reject_brand_updates_only(self):
        brand = {"id": 2, "name": "Acme Brand", "status": "rejected"}
        update_mock = AsyncMock(return_value=brand)

        with patch("app.services.brand_service.BrandRepository.update_brand_review", update_mock):
            result = await BrandService.reject_brand(2, reviewed_by="admin_user", review_notes="rejected info")
            self.assertEqual(result, brand)
            update_mock.assert_awaited_once_with(2, status="rejected", reviewed_by="admin_user", review_notes="rejected info")

    async def test_request_more_info_brand(self):
        brand = {"id": 2, "name": "Acme Brand", "status": "needs_more_info"}
        update_mock = AsyncMock(return_value=brand)

        with patch("app.services.brand_service.BrandRepository.update_brand_review", update_mock):
            result = await BrandService.request_more_info(2, reviewed_by="admin_user", review_notes="please provide url")
            self.assertEqual(result, brand)
            update_mock.assert_awaited_once_with(2, status="needs_more_info", reviewed_by="admin_user", review_notes="please provide url")


class RequireSuperadminTestCase(unittest.TestCase):
    def test_allows_real_superadmin_token(self):
        token = create_access_token({"user_id": 7, "role": "superadmin", "email": "superadmin@example.com"})
        payload = require_superadmin(f"Bearer {token}")
        self.assertEqual(payload["role"], "superadmin")

    def test_rejects_brand_admin_token(self):
        token = create_access_token({"user_id": 1, "role": "admin", "brand_id": 1, "email": "admin@example.com"})
        with self.assertRaises(HTTPException) as ctx:
            require_superadmin(f"Bearer {token}")
        self.assertEqual(ctx.exception.status_code, 403)

    def test_rejects_missing_token(self):
        with self.assertRaises(HTTPException) as ctx:
            require_superadmin("")
        self.assertEqual(ctx.exception.status_code, 401)
