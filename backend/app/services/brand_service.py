import uuid

from app.repositories.brand_repository import BrandRepository
from app.repositories.user_repository import UserRepository


class BrandService:
    @staticmethod
    async def create_brand(
        name: str,
        plan: str,
        *,
        company_name: str | None = None,
        business_url: str | None = None,
        onboarding_notes: str | None = None,
    ):
        torch_sub_id = f"torch_{uuid.uuid4().hex[:12]}"
        return await BrandRepository.insert_brand(
            name,
            plan,
            torch_sub_id,
            company_name=company_name,
            business_url=business_url,
            onboarding_notes=onboarding_notes,
        )

    @staticmethod
    async def list_pending_brands():
        return await BrandRepository.list_pending_brands()

    @staticmethod
    async def approve_brand(brand_id: int, *, reviewed_by: str | None = None, review_notes: str | None = None):
        brand = await BrandRepository.update_brand_review(
            brand_id,
            status="approved",
            reviewed_by=reviewed_by or "torchproxy-admin",
            review_notes=review_notes,
        )
        if brand is None:
            return None

        await UserRepository.activate_brand_owner_users(brand_id)
        return brand

    @staticmethod
    async def reject_brand(brand_id: int, *, reviewed_by: str | None = None, review_notes: str | None = None):
        return await BrandRepository.update_brand_review(
            brand_id,
            status="rejected",
            reviewed_by=reviewed_by or "torchproxy-admin",
            review_notes=review_notes,
        )

    @staticmethod
    async def request_more_info(brand_id: int, *, reviewed_by: str | None = None, review_notes: str | None = None):
        return await BrandRepository.update_brand_review(
            brand_id,
            status="needs_more_info",
            reviewed_by=reviewed_by or "torchproxy-admin",
            review_notes=review_notes,
        )
