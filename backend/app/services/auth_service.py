from app.core.auth import verify_password
from app.repositories.brand_repository import BrandRepository
from app.repositories.user_repository import UserRepository


class AuthService:
    @staticmethod
    async def login(email: str, password: str, brand_name: str | None = None):
        user = await UserRepository.get_user_by_email(email)
        if user is None:
            return None

        if not verify_password(password, user["password_hash"]):
            return None

        brand = await BrandRepository.get_brand_by_id(user["brand_id"])
        if brand is None:
            return None

        if brand_name is not None and brand_name.strip() and brand["name"] != brand_name.strip():
            return None

        return {
            "user": user,
            "brand": brand,
        }


class AdminService:
    @staticmethod
    async def onboard_brand(name: str, plan: str):
        return await BrandRepository.insert_brand(name, plan, f"torch_{name.lower().replace(' ', '_')}")

    @staticmethod
    async def create_user(brand_id: int, full_name: str, email: str, password: str, role: str):
        from app.core.auth import hash_password

        password_hash = hash_password(password)
        return await UserRepository.create_user(brand_id, full_name, email, password_hash, role)
