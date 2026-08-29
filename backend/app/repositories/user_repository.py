from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import db
from app.models import User


class UserRepository:
    _FIELDS = [
        "id",
        "brand_id",
        "full_name",
        "email",
        "password_hash",
        "role",
        "is_active",
        "is_brand_owner",
        "invite_accepted_at",
        "created_at",
    ]

    @staticmethod
    async def get_user_by_email(email: str, session: AsyncSession | None = None):
        async with db.session_scope(session) as s:
            stmt = select(User).where(User.email == email).limit(1)
            row = (await s.execute(stmt)).scalar_one_or_none()
            return db.model_to_dict(row, UserRepository._FIELDS)

    @staticmethod
    async def get_user_by_id(user_id: int, session: AsyncSession | None = None):
        async with db.session_scope(session) as s:
            row = await s.get(User, user_id)
            return db.model_to_dict(row, UserRepository._FIELDS)

    @staticmethod
    async def create_user(
        brand_id: int,
        full_name: str,
        email: str,
        password_hash: str,
        role: str,
        *,
        is_active: bool = True,
        is_brand_owner: bool = False,
        invite_accepted_at: datetime | str | None = None,
        session: AsyncSession | None = None,
        # Back-compat alias used by older call sites
        conn=None,
    ):
        session = session if session is not None else conn
        async with db.session_scope(session) as s:
            user = User(
                brand_id=brand_id,
                full_name=full_name,
                email=email,
                password_hash=password_hash,
                role=role,
                is_active=is_active,
                is_brand_owner=is_brand_owner,
                invite_accepted_at=invite_accepted_at,
            )
            s.add(user)
            await s.flush()
            await s.refresh(user)
            return db.model_to_dict(user, UserRepository._FIELDS)

    @staticmethod
    async def activate_brand_owner_users(brand_id: int, session: AsyncSession | None = None, conn=None):
        session = session if session is not None else conn
        async with db.session_scope(session) as s:
            await s.execute(
                update(User)
                .where(User.brand_id == brand_id, User.is_brand_owner.is_(True))
                .values(is_active=True)
            )

    @staticmethod
    async def set_user_password_and_activate(
        user_id: int,
        password_hash: str,
        session: AsyncSession | None = None,
        conn=None,
    ):
        session = session if session is not None else conn
        async with db.session_scope(session) as s:
            user = await s.get(User, user_id)
            if user is None:
                return None
            user.password_hash = password_hash
            user.is_active = True
            user.invite_accepted_at = datetime.utcnow()
            await s.flush()
            await s.refresh(user)
            return db.model_to_dict(user, UserRepository._FIELDS)
