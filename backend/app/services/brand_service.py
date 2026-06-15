import uuid

from app.repositories.brand_repository import BrandRepository


class BrandService:
    @staticmethod
    async def create_brand(name: str, plan: str):
        torch_sub_id = f"torch_{uuid.uuid4().hex[:12]}"
        return await BrandRepository.insert_brand(name, plan, torch_sub_id)

    @staticmethod
    async def onboard_brand(name: str, plan: str, current_user: dict):
        existing_brand = await BrandRepository.get_brand_by_name(name)

        if existing_brand is not None:
            if existing_brand["id"] != current_user["brand_id"]:
                raise PermissionError("Token does not belong to this brand")
            return existing_brand

        if current_user["role"] != "admin":
            raise PermissionError("Only admins can create a new brand")

        return await BrandService.create_brand(name, plan)
