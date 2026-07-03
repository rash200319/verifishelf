from datetime import date

from aiomysql.cursors import DictCursor

from app.core import db


class PromoRepository:
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
    ):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(
                    """
                    INSERT INTO promo_windows (
                        brand_id, product_id, marketplace_id, start_date, end_date, notes
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (brand_id, product_id, marketplace_id, start_date, end_date, notes),
                )
                promo_id = cur.lastrowid

                await cur.execute(
                    """
                    SELECT id, brand_id, product_id, marketplace_id, start_date, end_date, notes, created_at
                    FROM promo_windows
                    WHERE id = %s
                    """,
                    (promo_id,),
                )
                return PromoRepository._normalize_row(await cur.fetchone())

    @staticmethod
    async def list_promos(
        brand_id: int,
        product_id: int | None = None,
        active_on: date | None = None,
    ):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        query = """
            SELECT id, brand_id, product_id, marketplace_id, start_date, end_date, notes, created_at
            FROM promo_windows
            WHERE brand_id = %s
        """
        params: list = [brand_id]

        if product_id is not None:
            query += " AND product_id = %s"
            params.append(product_id)

        if active_on is not None:
            query += " AND start_date <= %s AND end_date >= %s"
            params.extend([active_on, active_on])

        query += " ORDER BY start_date DESC, id DESC"

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(query, tuple(params))
                rows = await cur.fetchall()
                return [PromoRepository._normalize_row(row) for row in rows]

    @staticmethod
    async def has_active_promo(
        brand_id: int,
        product_id: int,
        marketplace_id: int | None,
        check_date: date,
    ) -> bool:
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    SELECT COUNT(*) AS promo_count
                    FROM promo_windows
                    WHERE brand_id = %s
                      AND product_id = %s
                      AND start_date <= %s
                      AND end_date >= %s
                      AND (marketplace_id IS NULL OR marketplace_id = %s)
                    """,
                    (brand_id, product_id, check_date, check_date, marketplace_id),
                )
                row = await cur.fetchone()
                return int(row[0]) > 0
