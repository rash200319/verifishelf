import aiomysql

from app.core import db


class EnforcementLetterRepository:
    @staticmethod
    async def create_letter(violation_id: int, letter_content: str, generated_by: str = "template"):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    INSERT INTO enforcement_letters (violation_id, letter_content, generated_by)
                    VALUES (%s, %s, %s)
                    """,
                    (violation_id, letter_content, generated_by),
                )
                letter_id = cur.lastrowid

                await cur.execute(
                    """
                    SELECT id, violation_id, letter_content, generated_by, generated_at
                    FROM enforcement_letters
                    WHERE id = %s
                    """,
                    (letter_id,),
                )
                return await cur.fetchone()

    @staticmethod
    async def get_latest_for_violation(violation_id: int):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT id, violation_id, letter_content, generated_by, generated_at
                    FROM enforcement_letters
                    WHERE violation_id = %s
                    ORDER BY generated_at DESC, id DESC
                    LIMIT 1
                    """,
                    (violation_id,),
                )
                return await cur.fetchone()

    @staticmethod
    async def get_violation_context(violation_id: int, brand_id: int):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT
                        v.id AS violation_id,
                        v.map_price,
                        v.advertised_price,
                        v.price_delta_pct,
                        v.status,
                        v.detected_at,
                        l.listing_title,
                        l.listing_url,
                        l.currency_code,
                        p.name AS product_name,
                        b.name AS brand_name,
                        s.seller_name,
                        s.storefront_url
                    FROM violations v
                    INNER JOIN listings l ON l.id = v.listing_id
                    INNER JOIN products p ON p.id = l.product_id
                    INNER JOIN brands b ON b.id = p.brand_id
                    INNER JOIN sellers s ON s.id = l.seller_id
                    WHERE v.id = %s AND p.brand_id = %s
                    LIMIT 1
                    """,
                    (violation_id, brand_id),
                )
                return await cur.fetchone()
