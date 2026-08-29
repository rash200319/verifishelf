from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import db
from app.models import RawCrawlResult


class RawCrawlResultRepository:
    @staticmethod
    async def create_raw_result(
        crawl_job_id: int,
        brand_id: int,
        product_id: int,
        raw_html: str,
        session: AsyncSession | None = None,
    ):
        async with db.session_scope(session) as s:
            row = RawCrawlResult(
                crawl_job_id=crawl_job_id,
                brand_id=brand_id,
                product_id=product_id,
                raw_html=raw_html,
            )
            s.add(row)
            await s.flush()
            return row.id
