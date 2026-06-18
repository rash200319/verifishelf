from aiomysql.cursors import DictCursor

from app.core import db


class InviteRepository:
    @staticmethod
    async def create_invite(
        brand_id: int,
        email: str | None,
        role: str,
        invite_code_hash: str,
        expires_at: str,
        created_by: int | None = None,
        conn=None,
    ):
        if db.mysql_pool is None and conn is None:
            raise RuntimeError("MySQL pool is not initialized")

        if conn is None:
            async with db.mysql_pool.acquire() as pooled_conn:
                return await InviteRepository.create_invite(
                    brand_id,
                    email,
                    role,
                    invite_code_hash,
                    expires_at,
                    created_by=created_by,
                    conn=pooled_conn,
                )

        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                """
                INSERT INTO brand_invites (
                    brand_id,
                    email,
                    role,
                    invite_code_hash,
                    expires_at,
                    created_by
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (brand_id, email, role, invite_code_hash, expires_at, created_by),
            )

            invite_id = cur.lastrowid
            return await InviteRepository.get_invite_by_id(invite_id, conn=conn)

    @staticmethod
    async def get_invite_by_id(invite_id: int, conn=None):
        if db.mysql_pool is None and conn is None:
            raise RuntimeError("MySQL pool is not initialized")

        if conn is None:
            async with db.mysql_pool.acquire() as pooled_conn:
                return await InviteRepository.get_invite_by_id(invite_id, conn=pooled_conn)

        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                """
                SELECT
                    id,
                    brand_id,
                    email,
                    role,
                    invite_code_hash,
                    expires_at,
                    used_at,
                    created_by,
                    created_at
                FROM brand_invites
                WHERE id = %s
                LIMIT 1
                """,
                (invite_id,),
            )
            return await cur.fetchone()

    @staticmethod
    async def get_invite_by_hash(invite_code_hash: str, conn=None):
        if db.mysql_pool is None and conn is None:
            raise RuntimeError("MySQL pool is not initialized")

        if conn is None:
            async with db.mysql_pool.acquire() as pooled_conn:
                return await InviteRepository.get_invite_by_hash(invite_code_hash, conn=pooled_conn)

        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                """
                SELECT
                    id,
                    brand_id,
                    email,
                    role,
                    invite_code_hash,
                    expires_at,
                    used_at,
                    created_by,
                    created_at
                FROM brand_invites
                WHERE invite_code_hash = %s
                LIMIT 1
                """,
                (invite_code_hash,),
            )
            return await cur.fetchone()

    @staticmethod
    async def list_invites_by_brand(brand_id: int, conn=None):
        if db.mysql_pool is None and conn is None:
            raise RuntimeError("MySQL pool is not initialized")

        if conn is None:
            async with db.mysql_pool.acquire() as pooled_conn:
                return await InviteRepository.list_invites_by_brand(brand_id, conn=pooled_conn)

        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                """
                SELECT
                    id,
                    brand_id,
                    email,
                    role,
                    expires_at,
                    used_at,
                    created_by,
                    created_at
                FROM brand_invites
                WHERE brand_id = %s
                ORDER BY created_at DESC
                """,
                (brand_id,),
            )
            return await cur.fetchall()

    @staticmethod
    async def mark_invite_used(invite_id: int, conn=None):
        if db.mysql_pool is None and conn is None:
            raise RuntimeError("MySQL pool is not initialized")

        if conn is None:
            async with db.mysql_pool.acquire() as pooled_conn:
                return await InviteRepository.mark_invite_used(invite_id, conn=pooled_conn)

        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                """
                UPDATE brand_invites
                SET used_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (invite_id,),
            )
            return await InviteRepository.get_invite_by_id(invite_id, conn=conn)
