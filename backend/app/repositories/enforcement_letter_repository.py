from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import db
from app.models import (
    Brand,
    BrandMarketplace,
    EnforcementLetter,
    Listing,
    Product,
    Seller,
    Violation,
)


class EnforcementLetterRepository:
    _FIELDS = [
        "id",
        "violation_id",
        "letter_content",
        "generated_by",
        "screenshot_base64",
        "status",
        "sent_at",
        "generated_at",
    ]

    @staticmethod
    async def create_letter(
        violation_id: int,
        letter_content: str,
        generated_by: str = "template",
        screenshot_base64: str | None = None,
        session: AsyncSession | None = None,
    ):
        async with db.session_scope(session) as s:
            letter = EnforcementLetter(
                violation_id=violation_id,
                letter_content=letter_content,
                generated_by=generated_by,
                screenshot_base64=screenshot_base64,
            )
            s.add(letter)
            await s.flush()
            await s.refresh(letter)
            return db.model_to_dict(letter, EnforcementLetterRepository._FIELDS)

    @staticmethod
    async def get_latest_for_violation(violation_id: int, session: AsyncSession | None = None):
        async with db.session_scope(session) as s:
            stmt = (
                select(EnforcementLetter)
                .where(EnforcementLetter.violation_id == violation_id)
                .order_by(EnforcementLetter.generated_at.desc(), EnforcementLetter.id.desc())
                .limit(1)
            )
            row = (await s.execute(stmt)).scalar_one_or_none()
            return db.model_to_dict(row, EnforcementLetterRepository._FIELDS)

    @staticmethod
    async def mark_sent(letter_id: int, session: AsyncSession | None = None):
        async with db.session_scope(session) as s:
            letter = await s.get(EnforcementLetter, letter_id)
            if letter is None:
                return None
            letter.status = "sent"
            letter.sent_at = datetime.utcnow()
            await s.flush()
            await s.refresh(letter)
            return db.model_to_dict(letter, EnforcementLetterRepository._FIELDS)

    @staticmethod
    async def get_violation_context(
        violation_id: int,
        brand_id: int,
        session: AsyncSession | None = None,
    ):
        async with db.session_scope(session) as s:
            stmt = (
                select(
                    Violation.id.label("violation_id"),
                    Violation.map_price,
                    Violation.advertised_price,
                    Violation.price_delta_pct,
                    Violation.status,
                    Violation.detected_at,
                    Listing.listing_title,
                    Listing.listing_url,
                    Listing.currency_code,
                    Product.name.label("product_name"),
                    Brand.name.label("brand_name"),
                    Brand.torch_sub_id,
                    BrandMarketplace.country_code,
                    Seller.seller_name,
                    Seller.storefront_url,
                )
                .select_from(Violation)
                .join(Listing, Listing.id == Violation.listing_id)
                .join(Product, Product.id == Listing.product_id)
                .join(Brand, Brand.id == Product.brand_id)
                .join(Seller, Seller.id == Listing.seller_id)
                .outerjoin(
                    BrandMarketplace,
                    (BrandMarketplace.brand_id == Brand.id)
                    & (BrandMarketplace.marketplace_id == Listing.marketplace_id),
                )
                .where(Violation.id == violation_id, Product.brand_id == brand_id)
                .limit(1)
            )
            row = (await s.execute(stmt)).mappings().first()
            return dict(row) if row else None
