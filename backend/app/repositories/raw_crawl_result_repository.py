from aiomysql.cursors import DictCursor

from app.core import db


class RawCrawlResultRepository:
    @staticmethod
    async def create_raw_result(crawl_job_id: int, brand_id: int, product_id: int, raw_html: str):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO raw_crawl_results (crawl_job_id, brand_id, product_id, raw_html)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (crawl_job_id, brand_id, product_id, raw_html),
                )
                await conn.commit()
                return cur.lastrowid
