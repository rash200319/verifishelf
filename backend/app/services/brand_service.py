import uuid

from app.repositories.brand_repository import BrandRepository


class BrandService:
    @staticmethod
    async def create_brand(name: str, plan: str):
        torch_sub_id = f"torch_{uuid.uuid4().hex[:12]}"
        return await BrandRepository.insert_brand(name, plan, torch_sub_id)
