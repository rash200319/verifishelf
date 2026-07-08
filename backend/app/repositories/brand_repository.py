from aiomysql.cursors import DictCursor

from app.core import db


class BrandRepository:
    @staticmethod
    async def insert_brand(
        name: str,
        plan: str,
        torch_sub_id: str,
        *,
        company_name: str | None = None,
        business_url: str | None = None,
        onboarding_notes: str | None = None,
        status: str = "pending_review",
        conn=None,
    ):
        if db.mysql_pool is None and conn is None:
            raise RuntimeError("MySQL pool is not initialized")

        if conn is None:
            async with db.mysql_pool.acquire() as pooled_conn:
                return await BrandRepository.insert_brand(
                    name,
                    plan,
                    torch_sub_id,
                    company_name=company_name,
                    business_url=business_url,
                    onboarding_notes=onboarding_notes,
                    status=status,
                    conn=pooled_conn,
                )

        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                """
                INSERT INTO brands (
                    name,
                    plan,
                    status,
                    company_name,
                    business_url,
                    onboarding_notes,
                    torch_sub_id
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (name, plan, status, company_name, business_url, onboarding_notes, torch_sub_id),
            )

            brand_id = cur.lastrowid
            return await BrandRepository.get_brand_by_id(brand_id)

    @staticmethod
    async def get_brand_by_name(name: str, conn=None):
        if db.mysql_pool is None and conn is None:
            raise RuntimeError("MySQL pool is not initialized")

        if conn is None:
            async with db.mysql_pool.acquire() as pooled_conn:
                return await BrandRepository.get_brand_by_name(name, conn=pooled_conn)

        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                """
                SELECT
                    id,
                    name,
                    plan,
                    status,
                    company_name,
                    business_url,
                    onboarding_notes,
                    review_notes,
                    reviewed_by,
                    reviewed_at,
                    torch_sub_id,
                    created_at
                FROM brands
                WHERE name = %s
                LIMIT 1
                """,
                (name,),
            )
            return await cur.fetchone()

    @staticmethod
    async def get_brand_by_id(brand_id: int, conn=None):
        if db.mysql_pool is None and conn is None:
            raise RuntimeError("MySQL pool is not initialized")

        if conn is None:
            async with db.mysql_pool.acquire() as pooled_conn:
                return await BrandRepository.get_brand_by_id(brand_id, conn=pooled_conn)

        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                """
                SELECT
                    id,
                    name,
                    plan,
                    status,
                    company_name,
                    business_url,
                    onboarding_notes,
                    review_notes,
                    reviewed_by,
                    reviewed_at,
                    torch_sub_id,
                    created_at
                FROM brands
                WHERE id = %s
                LIMIT 1
                """,
                (brand_id,),
            )
            return await cur.fetchone()

    @staticmethod
    async def list_pending_brands(conn=None):
        if db.mysql_pool is None and conn is None:
            raise RuntimeError("MySQL pool is not initialized")

        if conn is None:
            async with db.mysql_pool.acquire() as pooled_conn:
                return await BrandRepository.list_pending_brands(conn=pooled_conn)

        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                """
                SELECT
                    id,
                    name,
                    plan,
                    status,
                    company_name,
                    business_url,
                    onboarding_notes,
                    review_notes,
                    reviewed_by,
                    reviewed_at,
                    torch_sub_id,
                    created_at
                FROM brands
                WHERE status = 'pending_review'
                ORDER BY created_at ASC
                """
            )
            return await cur.fetchall()

    @staticmethod
    async def update_brand_review(
        brand_id: int,
        *,
        status: str,
        reviewed_by: str | None = None,
        review_notes: str | None = None,
        conn=None,
    ):
        if db.mysql_pool is None and conn is None:
            raise RuntimeError("MySQL pool is not initialized")

        if conn is None:
            async with db.mysql_pool.acquire() as pooled_conn:
                return await BrandRepository.update_brand_review(
                    brand_id,
                    status=status,
                    reviewed_by=reviewed_by,
                    review_notes=review_notes,
                    conn=pooled_conn,
                )

        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                """
                UPDATE brands
                SET status = %s,
                    reviewed_by = %s,
                    reviewed_at = CURRENT_TIMESTAMP,
                    review_notes = %s
                WHERE id = %s
                """,
                (status, reviewed_by, review_notes, brand_id),
            )
            return await BrandRepository.get_brand_by_id(brand_id, conn=conn)

    @staticmethod
    async def update_brand_plan(
        brand_id: int,
        plan: str,
        torch_sub_id: str,
        conn=None,
    ):
        if db.mysql_pool is None and conn is None:
            raise RuntimeError("MySQL pool is not initialized")

        if conn is None:
            async with db.mysql_pool.acquire() as pooled_conn:
                return await BrandRepository.update_brand_plan(
                    brand_id,
                    plan,
                    torch_sub_id,
                    conn=pooled_conn,
                )

        async with conn.cursor(DictCursor) as cur:
            await cur.execute(
                """
                UPDATE brands
                SET plan = %s,
                    torch_sub_id = %s
                WHERE id = %s
                """,
                (plan, torch_sub_id, brand_id),
            )
            return await BrandRepository.get_brand_by_id(brand_id, conn=conn)
