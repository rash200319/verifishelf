from aiomysql.cursors import DictCursor

from app.core import db


class UserRepository:
    @staticmethod
    async def get_user_by_email(email: str, conn=None):
        if db.mysql_pool is None and conn is None:
            raise RuntimeError("MySQL pool is not initialized")

        if conn is None:
            async with db.mysql_pool.acquire() as pooled_conn:
                return await UserRepository.get_user_by_email(email, conn=pooled_conn)

        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                """
                SELECT
                    id,
                    brand_id,
                    full_name,
                    email,
                    password_hash,
                    role,
                    is_active,
                    is_brand_owner,
                    invite_accepted_at,
                    created_at
                FROM users
                WHERE email = %s
                LIMIT 1
                """,
                (email,),
            )
            return await cur.fetchone()

    @staticmethod
    async def get_user_by_id(user_id: int, conn=None):
        if db.mysql_pool is None and conn is None:
            raise RuntimeError("MySQL pool is not initialized")

        if conn is None:
            async with db.mysql_pool.acquire() as pooled_conn:
                return await UserRepository.get_user_by_id(user_id, conn=pooled_conn)

        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                """
                SELECT
                    id,
                    brand_id,
                    full_name,
                    email,
                    password_hash,
                    role,
                    is_active,
                    is_brand_owner,
                    invite_accepted_at,
                    created_at
                FROM users
                WHERE id = %s
                LIMIT 1
                """,
                (user_id,),
            )
            return await cur.fetchone()

    @staticmethod
    async def create_user(
        brand_id: int,
        full_name: str,
        email: str,
        password_hash: str,
        role: str,
        *,
        is_active: bool = True,
        is_brand_owner: bool = False,
        invite_accepted_at: str | None = None,
        conn=None,
    ):
        if db.mysql_pool is None and conn is None:
            raise RuntimeError("MySQL pool is not initialized")

        if conn is None:
            async with db.mysql_pool.acquire() as pooled_conn:
                return await UserRepository.create_user(
                    brand_id,
                    full_name,
                    email,
                    password_hash,
                    role,
                    is_active=is_active,
                    is_brand_owner=is_brand_owner,
                    invite_accepted_at=invite_accepted_at,
                    conn=pooled_conn,
                )

        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                """
                INSERT INTO users (
                    brand_id,
                    full_name,
                    email,
                    password_hash,
                    role,
                    is_active,
                    is_brand_owner,
                    invite_accepted_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (brand_id, full_name, email, password_hash, role, is_active, is_brand_owner, invite_accepted_at),
            )

            user_id = cur.lastrowid
            return await UserRepository.get_user_by_id(user_id, conn=conn)

    @staticmethod
    async def activate_brand_owner_users(brand_id: int, conn=None):
        if db.mysql_pool is None and conn is None:
            raise RuntimeError("MySQL pool is not initialized")

        if conn is None:
            async with db.mysql_pool.acquire() as pooled_conn:
                return await UserRepository.activate_brand_owner_users(brand_id, conn=pooled_conn)

        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                """
                UPDATE users
                SET is_active = TRUE
                WHERE brand_id = %s
                  AND is_brand_owner = TRUE
                """,
                (brand_id,),
            )

    @staticmethod
    async def set_user_password_and_activate(user_id: int, password_hash: str, conn=None):
        if db.mysql_pool is None and conn is None:
            raise RuntimeError("MySQL pool is not initialized")

        if conn is None:
            async with db.mysql_pool.acquire() as pooled_conn:
                return await UserRepository.set_user_password_and_activate(user_id, password_hash, conn=pooled_conn)

        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                """
                UPDATE users
                SET password_hash = %s,
                    is_active = TRUE,
                    invite_accepted_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (password_hash, user_id),
            )
            return await UserRepository.get_user_by_id(user_id, conn=conn)
