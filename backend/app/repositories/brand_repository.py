from aiomysql.cursors import DictCursor

from app.core import db


class BrandRepository:
    @staticmethod
    async def insert_brand(name: str, plan: str, torch_sub_id: str):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(
                    """
                    INSERT INTO brands (name, plan, torch_sub_id)
                    VALUES (%s, %s, %s)
                    """,
                    (name, plan, torch_sub_id),
                )

                brand_id = cur.lastrowid

                await cur.execute(
                    """
                    SELECT id, name, plan, torch_sub_id, created_at
                    FROM brands
                    WHERE id = %s
                    """,
                    (brand_id,),
                )
                return await cur.fetchone()
