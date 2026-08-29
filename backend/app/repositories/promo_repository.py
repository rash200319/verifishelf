from __future__ import annotations

from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import db
from app.models import PromoWindow


class PromoRepository:
    _FIELDS = [
        "id",
        "brand_id",
        "product_id",
        "marketplace_id",
        "start_date",
        "end_date",
        "notes",
        "created_at",
    ]

    @staticmethod
    def _normalize_row(row: dict) -> dict:
        return {
            "id": row["id"],
            "brand_id": row["brand_id"],
            "product_id": row["product_id"],
            "marketplace_id": row["marketplace_id"],
            "start_date": row["start_date"],
            "end_date": row["end_date"],
            "notes": row["notes"],
            "created_at": row["created_at"],
        }

    @staticmethod
    async def create_promo(
        brand_id: int,
        product_id: int,
        marketplace_id: int | None,
        start_date: date,
        end_date: date,
        notes: str | None,
        session: AsyncSession | None = None,
    ):
        async with db.session_scope(session) as s:
            promo = PromoWindow(
                brand_id=brand_id,
                product_id=product_id,
                marketplace_id=marketplace_id,
                start_date=start_date,
                end_date=end_date,
                notes=notes,
            )
            s.add(promo)
            await s.flush()
            await s.refresh(promo)
            return PromoRepository._normalize_row(db.model_to_dict(promo, PromoRepository._FIELDS))

    @staticmethod
    async def list_promos(
        brand_id: int,
        product_id: int | None = None,
        active_on: date | None = None,
        session: AsyncSession | None = None,
    ):
        async with db.session_scope(session) as s:
            stmt = select(PromoWindow).where(PromoWindow.brand_id == brand_id)
            if product_id is not None:
                stmt = stmt.where(PromoWindow.product_id == product_id)
            if active_on is not None:
                stmt = stmt.where(
                    PromoWindow.start_date <= active_on,
                    PromoWindow.end_date >= active_on,
                )
            stmt = stmt.order_by(PromoWindow.start_date.desc(), PromoWindow.id.desc())
            rows = (await s.execute(stmt)).scalars().all()
            return [
                PromoRepository._normalize_row(db.model_to_dict(row, PromoRepository._FIELDS))
                for row in rows
            ]

    @staticmethod
    async def has_active_promo(
        brand_id: int,
        product_id: int,
        marketplace_id: int | None,
        check_date: date,
        session: AsyncSession | None = None,
    ) -> bool:
        async with db.session_scope(session) as s:
            stmt = (
                select(func.count())
                .select_from(PromoWindow)
                .where(
                    PromoWindow.brand_id == brand_id,
                    PromoWindow.product_id == product_id,
                    PromoWindow.start_date <= check_date,
                    PromoWindow.end_date >= check_date,
                    or_(
                        PromoWindow.marketplace_id.is_(None),
                        PromoWindow.marketplace_id == marketplace_id,
                    ),
                )
            )
            count = (await s.execute(stmt)).scalar_one()
            return int(count) > 0
