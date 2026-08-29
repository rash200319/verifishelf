from __future__ import annotations

from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import db
from app.models import Brand


class BrandRepository:
    _FIELDS = [
        "id",
        "name",
        "plan",
        "status",
        "company_name",
        "business_url",
        "onboarding_notes",
        "review_notes",
        "reviewed_by",
        "reviewed_at",
        "torch_sub_id",
        "registration_number",
        "business_address",
        "industry",
        "contact_title",
        "contact_phone",
        "estimated_sku_range",
        "current_marketplaces",
        "authorized_attestation",
        "created_at",
    ]

    @staticmethod
    async def insert_brand(
        name: str,
        plan: str,
        torch_sub_id: str,
        *,
        company_name: str | None = None,
        business_url: str | None = None,
        onboarding_notes: str | None = None,
        status: str = "pending_review",
        registration_number: str | None = None,
        business_address: str | None = None,
        industry: str | None = None,
        contact_title: str | None = None,
        contact_phone: str | None = None,
        estimated_sku_range: str | None = None,
        current_marketplaces: str | None = None,
        authorized_attestation: bool = False,
        session: AsyncSession | None = None,
        conn=None,
    ):
        session = session if session is not None else conn
        async with db.session_scope(session) as s:
            brand = Brand(
                name=name,
                plan=plan,
                status=status,
                company_name=company_name,
                business_url=business_url,
                onboarding_notes=onboarding_notes,
                torch_sub_id=torch_sub_id,
                registration_number=registration_number,
                business_address=business_address,
                industry=industry,
                contact_title=contact_title,
                contact_phone=contact_phone,
                estimated_sku_range=estimated_sku_range,
                current_marketplaces=current_marketplaces,
                authorized_attestation=authorized_attestation,
            )
            s.add(brand)
            await s.flush()
            await s.refresh(brand)
            return db.model_to_dict(brand, BrandRepository._FIELDS)

    @staticmethod
    async def get_brand_by_name(name: str, session: AsyncSession | None = None, conn=None):
        session = session if session is not None else conn
        async with db.session_scope(session) as s:
            stmt = select(Brand).where(Brand.name == name).limit(1)
            row = (await s.execute(stmt)).scalar_one_or_none()
            return db.model_to_dict(row, BrandRepository._FIELDS)

    @staticmethod
    async def get_brand_by_id(brand_id: int, session: AsyncSession | None = None, conn=None):
        session = session if session is not None else conn
        async with db.session_scope(session) as s:
            row = await s.get(Brand, brand_id)
            return db.model_to_dict(row, BrandRepository._FIELDS)

    @staticmethod
    async def list_approved_brands(session: AsyncSession | None = None, conn=None):
        session = session if session is not None else conn
        async with db.session_scope(session) as s:
            stmt = (
                select(Brand.id, Brand.name)
                .where(Brand.status == "approved")
                .order_by(Brand.id.asc())
            )
            rows = (await s.execute(stmt)).mappings().all()
            return [dict(row) for row in rows]

    @staticmethod
    async def list_pending_brands(session: AsyncSession | None = None, conn=None):
        session = session if session is not None else conn
        async with db.session_scope(session) as s:
            stmt = (
                select(Brand)
                .where(Brand.status == "pending_review")
                .order_by(Brand.created_at.asc())
            )
            rows = (await s.execute(stmt)).scalars().all()
            return [db.model_to_dict(row, BrandRepository._FIELDS) for row in rows]

    @staticmethod
    async def update_brand_review(
        brand_id: int,
        *,
        status: str,
        reviewed_by: str | None = None,
        review_notes: str | None = None,
        session: AsyncSession | None = None,
        conn=None,
    ):
        session = session if session is not None else conn
        async with db.session_scope(session) as s:
            brand = await s.get(Brand, brand_id)
            if brand is None:
                return None
            brand.status = status
            brand.reviewed_by = reviewed_by
            brand.reviewed_at = datetime.utcnow()
            brand.review_notes = review_notes
            await s.flush()
            await s.refresh(brand)
            return db.model_to_dict(brand, BrandRepository._FIELDS)

    @staticmethod
    async def update_brand_plan(
        brand_id: int,
        plan: str,
        torch_sub_id: str,
        session: AsyncSession | None = None,
        conn=None,
    ):
        session = session if session is not None else conn
        async with db.session_scope(session) as s:
            brand = await s.get(Brand, brand_id)
            if brand is None:
                return None
            brand.plan = plan
            brand.torch_sub_id = torch_sub_id
            await s.flush()
            await s.refresh(brand)
            return db.model_to_dict(brand, BrandRepository._FIELDS)
