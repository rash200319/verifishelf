from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import db
from app.models import PriceSnapshot


class PriceSnapshotRepository:
    @staticmethod
    async def create_price_snapshot(
        listing_id: int,
        product_id: int,
        seller_id: int,
        price: float,
        session: AsyncSession | None = None,
    ):
        async with db.session_scope(session) as s:
            snapshot = PriceSnapshot(
                listing_id=listing_id,
                product_id=product_id,
                seller_id=seller_id,
                price=price,
            )
            s.add(snapshot)
            await s.flush()
            await s.refresh(snapshot)
            return db.model_to_dict(
                snapshot,
                ["id", "listing_id", "product_id", "seller_id", "price", "snapshot_time"],
            )
