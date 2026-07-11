from aiomysql.cursors import DictCursor

from app.core import db


class ProductRepository:
    @staticmethod
    async def get_product_for_brand(product_id: int, brand_id: int):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT id, brand_id, name, description, map_price, created_at
                    FROM products
                    WHERE id = %s AND brand_id = %s
                    LIMIT 1
                    """,
                    (product_id, brand_id),
                )
                return await cur.fetchone()

    @staticmethod
    async def list_products_for_brand(brand_id: int):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT id, brand_id, name, description, map_price, created_at
                    FROM products
                    WHERE brand_id = %s
                    ORDER BY id
                    """,
                    (brand_id,),
                )
                return await cur.fetchall()

    @staticmethod
    async def create_product(brand_id: int, name: str, description: str | None, map_price: float):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(
                    """
                    INSERT INTO products (brand_id, name, description, map_price)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (brand_id, name, description, map_price),
                )
                product_id = cur.lastrowid

                await cur.execute(
                    """
                    SELECT id, brand_id, name, description, map_price, created_at
                    FROM products
                    WHERE id = %s
                    """,
                    (product_id,),
                )
                return await cur.fetchone()

    @staticmethod
    async def update_product(product_id: int, brand_id: int, name: str, description: str | None, map_price: float):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(
                    """
                    UPDATE products
                    SET name = %s, description = %s, map_price = %s
                    WHERE id = %s AND brand_id = %s
                    """,
                    (name, description, map_price, product_id, brand_id),
                )
                if cur.rowcount == 0:
                    # Either the product doesn't exist, or it belongs to a
                    # different brand -- both cases are "not found" from this
                    # brand's perspective, never leak cross-brand existence.
                    existing = await ProductRepository.get_product_for_brand(product_id, brand_id)
                    if existing is None:
                        return None

                await cur.execute(
                    """
                    SELECT id, brand_id, name, description, map_price, created_at
                    FROM products
                    WHERE id = %s AND brand_id = %s
                    """,
                    (product_id, brand_id),
                )
                return await cur.fetchone()

    @staticmethod
    async def list_brand_product_targets():
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT
                        b.id AS brand_id,
                        b.name AS brand_name,
                        b.plan AS brand_plan,
                        p.id AS product_id,
                        p.name AS product_name
                    FROM brands b
                    INNER JOIN products p ON p.brand_id = b.id
                    ORDER BY b.id, p.id
                    """
                )
                return await cur.fetchall()
