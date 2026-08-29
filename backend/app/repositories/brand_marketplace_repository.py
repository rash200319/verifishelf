from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import db
from app.models import Brand, BrandMarketplace, Marketplace


class BrandMarketplaceRepository:
    @staticmethod
    async def list_enabled_approved(session: AsyncSession | None = None) -> list[dict]:
        async with db.session_scope(session) as s:
            stmt = (
                select(
                    BrandMarketplace.id.label("brand_marketplace_id"),
                    BrandMarketplace.brand_id,
                    BrandMarketplace.marketplace_id,
                    BrandMarketplace.enabled,
                    BrandMarketplace.crawl_frequency_hrs,
                    BrandMarketplace.country_code,
                    BrandMarketplace.priority,
                    Brand.name.label("brand_name"),
                    Brand.plan.label("brand_plan"),
                    Marketplace.name.label("marketplace_name"),
                    Marketplace.country_code.label("marketplace_country_code"),
                )
                .join(Brand, Brand.id == BrandMarketplace.brand_id)
                .join(Marketplace, Marketplace.id == BrandMarketplace.marketplace_id)
                .where(BrandMarketplace.enabled.is_(True), Brand.status == "approved")
                .order_by(
                    BrandMarketplace.brand_id,
                    BrandMarketplace.priority.asc(),
                    BrandMarketplace.marketplace_id.asc(),
                )
            )
            rows = (await s.execute(stmt)).mappings().all()
            return [dict(row) for row in rows]

    @staticmethod
    async def get_primary_enabled_for_brand(
        brand_id: int,
        session: AsyncSession | None = None,
    ) -> dict | None:
        async with db.session_scope(session) as s:
            stmt = (
                select(
                    BrandMarketplace.marketplace_id,
                    BrandMarketplace.country_code,
                    Marketplace.country_code.label("marketplace_country_code"),
                )
                .join(Brand, Brand.id == BrandMarketplace.brand_id)
                .join(Marketplace, Marketplace.id == BrandMarketplace.marketplace_id)
                .where(
                    BrandMarketplace.brand_id == brand_id,
                    BrandMarketplace.enabled.is_(True),
                    Brand.status == "approved",
                )
                .order_by(BrandMarketplace.priority.asc(), BrandMarketplace.marketplace_id.asc())
                .limit(1)
            )
            row = (await s.execute(stmt)).mappings().first()
            return dict(row) if row else None
