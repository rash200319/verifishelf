from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import db
from app.models import CrawlJob


class CrawlJobRepository:
    _FIELDS = [
        "id",
        "brand_id",
        "marketplace_id",
        "status",
        "started_at",
        "finished_at",
        "created_at",
    ]

    @staticmethod
    def _normalize_row(row: dict) -> dict:
        return {
            "id": row["id"],
            "brand_id": row["brand_id"],
            "marketplace_id": row["marketplace_id"],
            "status": row["status"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "created_at": row["created_at"],
        }

    @staticmethod
    async def create_job(
        brand_id: int,
        marketplace_id: int,
        status: str = "queued",
        session: AsyncSession | None = None,
    ):
        async with db.session_scope(session) as s:
            job = CrawlJob(
                brand_id=brand_id,
                marketplace_id=marketplace_id,
                status=status,
            )
            s.add(job)
            await s.flush()
            await s.refresh(job)
            return CrawlJobRepository._normalize_row(
                db.model_to_dict(job, CrawlJobRepository._FIELDS)
            )

    @staticmethod
    async def update_job_status(
        job_id: int,
        status: str,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        session: AsyncSession | None = None,
    ):
        async with db.session_scope(session) as s:
            job = await s.get(CrawlJob, job_id)
            if job is None:
                return None

            job.status = status
            if started_at is not None:
                job.started_at = started_at
            if finished_at is not None:
                job.finished_at = finished_at
            await s.flush()
            await s.refresh(job)
            return CrawlJobRepository._normalize_row(
                db.model_to_dict(job, CrawlJobRepository._FIELDS)
            )

    @staticmethod
    async def get_latest_job(
        brand_id: int,
        marketplace_id: int,
        session: AsyncSession | None = None,
    ):
        async with db.session_scope(session) as s:
            stmt = (
                select(CrawlJob)
                .where(
                    CrawlJob.brand_id == brand_id,
                    CrawlJob.marketplace_id == marketplace_id,
                )
                .order_by(CrawlJob.created_at.desc(), CrawlJob.id.desc())
                .limit(1)
            )
            row = (await s.execute(stmt)).scalar_one_or_none()
            if row is None:
                return None
            return CrawlJobRepository._normalize_row(
                db.model_to_dict(row, CrawlJobRepository._FIELDS)
            )

    @staticmethod
    async def list_jobs_for_brand(
        brand_id: int,
        limit: int = 20,
        session: AsyncSession | None = None,
    ):
        async with db.session_scope(session) as s:
            stmt = (
                select(CrawlJob)
                .where(CrawlJob.brand_id == brand_id)
                .order_by(CrawlJob.created_at.desc(), CrawlJob.id.desc())
                .limit(limit)
            )
            rows = (await s.execute(stmt)).scalars().all()
            return [
                CrawlJobRepository._normalize_row(db.model_to_dict(row, CrawlJobRepository._FIELDS))
                for row in rows
            ]

    @staticmethod
    async def get_job(
        job_id: int,
        brand_id: int | None = None,
        session: AsyncSession | None = None,
    ):
        async with db.session_scope(session) as s:
            stmt = select(CrawlJob).where(CrawlJob.id == job_id)
            if brand_id is not None:
                stmt = stmt.where(CrawlJob.brand_id == brand_id)
            stmt = stmt.limit(1)
            row = (await s.execute(stmt)).scalar_one_or_none()
            if row is None:
                return None
            return CrawlJobRepository._normalize_row(
                db.model_to_dict(row, CrawlJobRepository._FIELDS)
            )
