from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import db
from app.models import Listing


class ListingRepository:
    _FIELDS = [
        "id",
        "product_id",
        "seller_id",
        "marketplace_id",
        "listing_title",
        "listing_url",
        "image_url",
        "advertised_price",
        "currency_code",
        "scraped_at",
    ]

    @staticmethod
    def _row_to_dict(row) -> dict:
        return db.model_to_dict(row, ListingRepository._FIELDS)

    @staticmethod
    async def find_listing(
        product_id: int,
        seller_id: int,
        marketplace_id: int,
        session: AsyncSession | None = None,
    ):
        async with db.session_scope(session) as s:
            stmt = (
                select(Listing)
                .where(
                    Listing.product_id == product_id,
                    Listing.seller_id == seller_id,
                    Listing.marketplace_id == marketplace_id,
                )
                .order_by(Listing.id.desc())
                .limit(1)
            )
            row = (await s.execute(stmt)).scalar_one_or_none()
            return ListingRepository._row_to_dict(row)

    @staticmethod
    async def create_listing(
        product_id: int,
        seller_id: int,
        marketplace_id: int,
        listing_title: str,
        listing_url: str,
        image_url: str | None,
        advertised_price: float,
        currency_code: str,
        session: AsyncSession | None = None,
    ):
        async with db.session_scope(session) as s:
            listing = Listing(
                product_id=product_id,
                seller_id=seller_id,
                marketplace_id=marketplace_id,
                listing_title=listing_title,
                listing_url=listing_url,
                image_url=image_url,
                advertised_price=advertised_price,
                currency_code=currency_code,
            )
            s.add(listing)
            await s.flush()
            await s.refresh(listing)
            return ListingRepository._row_to_dict(listing)

    @staticmethod
    async def update_listing(
        listing_id: int,
        listing_title: str,
        listing_url: str,
        image_url: str | None,
        advertised_price: float,
        currency_code: str,
        session: AsyncSession | None = None,
    ):
        async with db.session_scope(session) as s:
            listing = await s.get(Listing, listing_id)
            if listing is None:
                return None

            listing.listing_title = listing_title
            listing.listing_url = listing_url
            listing.image_url = image_url
            listing.advertised_price = advertised_price
            listing.currency_code = currency_code
            listing.scraped_at = datetime.utcnow()
            await s.flush()
            await s.refresh(listing)
            return ListingRepository._row_to_dict(listing)
