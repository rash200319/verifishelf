from __future__ import annotations

import uuid

from app.core import db
from app.core.auth import hash_password, verify_password
from app.repositories.brand_repository import BrandRepository
from app.repositories.invite_repository import InviteRepository
from app.repositories.user_repository import UserRepository
from app.services.brand_service import BrandService
from app.services.invite_service import InviteService


class AuthService:
    @staticmethod
    async def register_brand_owner(
        full_name: str,
        email: str,
        password: str,
        brand_name: str,
        business_url: str,
        company_name: str,
        notes: str | None = None,
    ):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            await conn.begin()
            try:
                existing_user = await UserRepository.get_user_by_email(email, conn=conn)
                if existing_user is not None:
                    raise ValueError("Email already registered")

                existing_brand = await BrandRepository.get_brand_by_name(brand_name, conn=conn)
                if existing_brand is not None:
                    raise ValueError("Brand name already exists")

                brand = await BrandRepository.insert_brand(
                    brand_name,
                    "starter",
                    f"torch_{uuid.uuid4().hex[:12]}",
                    company_name=company_name,
                    business_url=business_url,
                    onboarding_notes=notes,
                    status="pending_review",
                    conn=conn,
                )
                if brand is None:
                    raise RuntimeError("Failed to create brand")

                user = await UserRepository.create_user(
                    brand["id"],
                    full_name,
                    email,
                    hash_password(password),
                    "admin",
                    is_active=False,
                    is_brand_owner=True,
                    conn=conn,
                )
                if user is None:
                    raise RuntimeError("Failed to create user")

                await conn.commit()
                return {
                    "brand": brand,
                    "user": user,
                }
            except Exception:
                await conn.rollback()
                raise

    @staticmethod
    async def login(email: str, password: str):
        user = await UserRepository.get_user_by_email(email)
        if user is None:
            return None

        if not verify_password(password, user["password_hash"]):
            return None

        brand = await BrandRepository.get_brand_by_id(user["brand_id"])
        if brand is None:
            return None

        # Allow login for approved brands OR pending brands that have completed onboarding
        # This allows brand admins to complete onboarding after payment
        if brand["status"] not in ("approved", "pending_review"):
            return None

        if not user.get("is_active"):
            return None

        return {
            "user": user,
            "brand": brand,
        }

    @staticmethod
    async def join_with_invite(email: str, invite_code: str, full_name: str, password: str):
        return await InviteService.join_with_invite(email, invite_code, full_name, password)

    @staticmethod
    async def get_registration_status(email: str):
        user = await UserRepository.get_user_by_email(email)
        if user is None:
            return None
        brand = await BrandRepository.get_brand_by_id(user["brand_id"])
        if brand is None:
            return None
        return {
            "brand_name": brand["name"],
            "status": brand["status"],
        }


class AdminService:
    @staticmethod
    async def onboard_brand(
        name: str,
        plan: str,
        *,
        company_name: str | None = None,
        business_url: str | None = None,
        onboarding_notes: str | None = None,
    ):
        return await BrandService.create_brand(
            name,
            plan,
            company_name=company_name,
            business_url=business_url,
            onboarding_notes=onboarding_notes,
        )

    @staticmethod
    async def create_user(brand_id: int, full_name: str, email: str, password: str, role: str):
        password_hash = hash_password(password)
        return await UserRepository.create_user(brand_id, full_name, email, password_hash, role)


class InviteAdminService:
    @staticmethod
    async def create_invite(
        brand_id: int,
        email: str | None,
        role: str,
        expires_in_minutes: int,
        created_by: int | None = None,
    ):
        return await InviteService.create_invite(
            brand_id,
            email=email,
            role=role,
            expires_in_minutes=expires_in_minutes,
            created_by=created_by,
        )

    @staticmethod
    async def list_invites(brand_id: int):
        return await InviteService.list_invites(brand_id)


class ReviewService:
    @staticmethod
    async def list_pending_brands():
        return await BrandService.list_pending_brands()

    @staticmethod
    async def approve_brand(brand_id: int, reviewed_by: str | None = None, review_notes: str | None = None):
        return await BrandService.approve_brand(
            brand_id,
            reviewed_by=reviewed_by,
            review_notes=review_notes,
        )

    @staticmethod
    async def reject_brand(brand_id: int, reviewed_by: str | None = None, review_notes: str | None = None):
        return await BrandService.reject_brand(
            brand_id,
            reviewed_by=reviewed_by,
            review_notes=review_notes,
        )

    @staticmethod
    async def request_more_info(brand_id: int, reviewed_by: str | None = None, review_notes: str | None = None):
        return await BrandService.request_more_info(
            brand_id,
            reviewed_by=reviewed_by,
            review_notes=review_notes,
        )
