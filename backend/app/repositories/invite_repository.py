from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import db
from app.models import BrandInvite


class InviteRepository:
    _FIELDS = [
        "id",
        "brand_id",
        "email",
        "role",
        "invite_code_hash",
        "expires_at",
        "used_at",
        "created_by",
        "created_at",
    ]

    _LIST_FIELDS = [
        "id",
        "brand_id",
        "email",
        "role",
        "expires_at",
        "used_at",
        "created_by",
        "created_at",
    ]

    @staticmethod
    async def create_invite(
        brand_id: int,
        email: str | None,
        role: str,
        invite_code_hash: str,
        expires_at: datetime | str,
        created_by: int | None = None,
        session: AsyncSession | None = None,
        conn=None,
    ):
        session = session if session is not None else conn
        async with db.session_scope(session) as s:
            invite = BrandInvite(
                brand_id=brand_id,
                email=email,
                role=role,
                invite_code_hash=invite_code_hash,
                expires_at=expires_at,
                created_by=created_by,
            )
            s.add(invite)
            await s.flush()
            await s.refresh(invite)
            return db.model_to_dict(invite, InviteRepository._FIELDS)

    @staticmethod
    async def get_invite_by_id(invite_id: int, session: AsyncSession | None = None, conn=None):
        session = session if session is not None else conn
        async with db.session_scope(session) as s:
            row = await s.get(BrandInvite, invite_id)
            return db.model_to_dict(row, InviteRepository._FIELDS)

    @staticmethod
    async def get_invite_by_hash(
        invite_code_hash: str,
        session: AsyncSession | None = None,
        conn=None,
    ):
        session = session if session is not None else conn
        async with db.session_scope(session) as s:
            stmt = (
                select(BrandInvite)
                .where(BrandInvite.invite_code_hash == invite_code_hash)
                .limit(1)
            )
            row = (await s.execute(stmt)).scalar_one_or_none()
            return db.model_to_dict(row, InviteRepository._FIELDS)

    @staticmethod
    async def list_invites_by_brand(
        brand_id: int,
        session: AsyncSession | None = None,
        conn=None,
    ):
        session = session if session is not None else conn
        async with db.session_scope(session) as s:
            stmt = (
                select(BrandInvite)
                .where(BrandInvite.brand_id == brand_id)
                .order_by(BrandInvite.created_at.desc())
            )
            rows = (await s.execute(stmt)).scalars().all()
            return [db.model_to_dict(row, InviteRepository._LIST_FIELDS) for row in rows]

    @staticmethod
    async def mark_invite_used(invite_id: int, session: AsyncSession | None = None, conn=None):
        session = session if session is not None else conn
        async with db.session_scope(session) as s:
            invite = await s.get(BrandInvite, invite_id)
            if invite is None:
                return None
            invite.used_at = datetime.utcnow()
            await s.flush()
            await s.refresh(invite)
            return db.model_to_dict(invite, InviteRepository._FIELDS)
