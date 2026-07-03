import hashlib
import secrets
from datetime import datetime, timedelta

from app.core import db
from app.core.auth import hash_password
from app.repositories.brand_repository import BrandRepository
from app.repositories.invite_repository import InviteRepository
from app.repositories.user_repository import UserRepository


def _hash_invite_code(invite_code: str) -> str:
    return hashlib.sha256(invite_code.encode("utf-8")).hexdigest()


class InviteService:
    @staticmethod
    async def create_invite(
        brand_id: int,
        *,
        email: str | None,
        role: str,
        expires_in_minutes: int,
        created_by: int | None = None,
    ):
        raw_code = secrets.token_urlsafe(16)
        invite_code_hash = _hash_invite_code(raw_code)
        expires_at = datetime.utcnow() + timedelta(minutes=expires_in_minutes)

        invite = await InviteRepository.create_invite(
            brand_id=brand_id,
            email=email,
            role=role,
            invite_code_hash=invite_code_hash,
            expires_at=expires_at,
            created_by=created_by,
        )

        if invite is None:
            return None

        return {
            "invite": invite,
            "invite_code": raw_code,
        }

    @staticmethod
    async def list_invites(brand_id: int):
        return await InviteRepository.list_invites_by_brand(brand_id)

    @staticmethod
    async def join_with_invite(email: str, invite_code: str, full_name: str, password: str):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            await conn.begin()
            try:
                invite = await InviteRepository.get_invite_by_hash(_hash_invite_code(invite_code), conn=conn)
                if invite is None:
                    await conn.rollback()
                    return None

                if invite["used_at"] is not None:
                    await conn.rollback()
                    return None

                if invite["expires_at"] is not None and invite["expires_at"] < datetime.utcnow():
                    await conn.rollback()
                    return None

                if invite["email"] and invite["email"].strip().lower() != email.strip().lower():
                    await conn.rollback()
                    return None

                existing_user = await UserRepository.get_user_by_email(email, conn=conn)
                if existing_user is not None:
                    await conn.rollback()
                    return None

                brand = await BrandRepository.get_brand_by_id(invite["brand_id"], conn=conn)
                if brand is None:
                    await conn.rollback()
                    return None

                password_hash = hash_password(password)
                user = await UserRepository.create_user(
                    invite["brand_id"],
                    full_name,
                    email,
                    password_hash,
                    invite["role"],
                    is_active=True,
                    is_brand_owner=False,
                    invite_accepted_at=datetime.utcnow(),
                    conn=conn,
                )
                await InviteRepository.mark_invite_used(invite["id"], conn=conn)
                await conn.commit()

                return {
                    "user": user,
                    "brand": brand,
                    "invite": invite,
                }
            except Exception:
                await conn.rollback()
                raise
