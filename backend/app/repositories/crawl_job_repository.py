from datetime import datetime

from aiomysql.cursors import DictCursor

from app.core import db


class CrawlJobRepository:
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
    async def create_job(brand_id: int, marketplace_id: int, status: str = "queued"):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(
                    """
                    INSERT INTO crawl_jobs (brand_id, marketplace_id, status)
                    VALUES (%s, %s, %s)
                    """,
                    (brand_id, marketplace_id, status),
                )
                job_id = cur.lastrowid

                await cur.execute(
                    """
                    SELECT id, brand_id, marketplace_id, status, started_at, finished_at, created_at
                    FROM crawl_jobs
                    WHERE id = %s
                    """,
                    (job_id,),
                )
                return CrawlJobRepository._normalize_row(await cur.fetchone())

    @staticmethod
    async def update_job_status(job_id: int, status: str, started_at: datetime | None = None, finished_at: datetime | None = None):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(
                    """
                    UPDATE crawl_jobs
                    SET status = %s,
                        started_at = COALESCE(%s, started_at),
                        finished_at = COALESCE(%s, finished_at)
                    WHERE id = %s
                    """,
                    (status, started_at, finished_at, job_id),
                )

                await cur.execute(
                    """
                    SELECT id, brand_id, marketplace_id, status, started_at, finished_at, created_at
                    FROM crawl_jobs
                    WHERE id = %s
                    """,
                    (job_id,),
                )
                row = await cur.fetchone()
                return CrawlJobRepository._normalize_row(row) if row else None

    @staticmethod
    async def get_latest_job(brand_id: int, marketplace_id: int):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT id, brand_id, marketplace_id, status, started_at, finished_at, created_at
                    FROM crawl_jobs
                    WHERE brand_id = %s AND marketplace_id = %s
                    ORDER BY created_at DESC, id DESC
                    LIMIT 1
                    """,
                    (brand_id, marketplace_id),
                )
                row = await cur.fetchone()
                if row is None:
                    return None
                return CrawlJobRepository._normalize_row(row)

    @staticmethod
    async def list_jobs_for_brand(brand_id: int, limit: int = 20):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT id, brand_id, marketplace_id, status, started_at, finished_at, created_at
                    FROM crawl_jobs
                    WHERE brand_id = %s
                    ORDER BY created_at DESC, id DESC
                    LIMIT %s
                    """,
                    (brand_id, limit),
                )
                rows = await cur.fetchall()
                return [CrawlJobRepository._normalize_row(row) for row in rows]

    @staticmethod
    async def get_job(job_id: int, brand_id: int | None = None):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        query = """
            SELECT id, brand_id, marketplace_id, status, started_at, finished_at, created_at
            FROM crawl_jobs
            WHERE id = %s
        """
        params: list = [job_id]

        if brand_id is not None:
            query += " AND brand_id = %s"
            params.append(brand_id)

        query += " LIMIT 1"

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(query, tuple(params))
                row = await cur.fetchone()
                if row is None:
                    return None
                return CrawlJobRepository._normalize_row(row)
