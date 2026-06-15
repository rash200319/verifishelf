from aiomysql.cursors import DictCursor

from app.core import db


class UserRepository:
    @staticmethod
    async def get_user_by_email(email: str):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT id, brand_id, full_name, email, password_hash, role
                    FROM users
                    WHERE email = %s
                    LIMIT 1
                    """,
                    (email,),
                )
                return await cur.fetchone()

    @staticmethod
    async def create_user(brand_id: int, full_name: str, email: str, password_hash: str, role: str):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(
                    """
                    INSERT INTO users (brand_id, full_name, email, password_hash, role)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (brand_id, full_name, email, password_hash, role),
                )

                user_id = cur.lastrowid

                await cur.execute(
                    """
                    SELECT id, brand_id, full_name, email, password_hash, role, created_at
                    FROM users
                    WHERE id = %s
                    """,
                    (user_id,),
                )
                return await cur.fetchone()
