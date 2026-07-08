import json

import aiomysql

from app.core import db


class SellerRepository:
    @staticmethod
    def _normalize_row(row: dict) -> dict:
        embedding = row.get("embedding")
        if isinstance(embedding, str):
            try:
                embedding = json.loads(embedding)
            except json.JSONDecodeError:
                embedding = None
        return {
            "id": row["id"],
            "cluster_id": row.get("cluster_id"),
            "seller_name": row["seller_name"],
            "storefront_url": row.get("storefront_url"),
            "embedding": embedding,
            "created_at": row.get("created_at"),
        }

    @staticmethod
    async def find_by_signature_hash(signature_hash: str):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT id, cluster_id, seller_name, storefront_url, embedding, created_at
                    FROM sellers
                    WHERE JSON_UNQUOTE(JSON_EXTRACT(embedding, '$.signature_hash')) = %s
                    LIMIT 1
                    """,
                    (signature_hash,),
                )
                row = await cur.fetchone()
                return SellerRepository._normalize_row(row) if row else None

    @staticmethod
    async def find_by_normalized_name(normalized_name: str):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT id, cluster_id, seller_name, storefront_url, embedding, created_at
                    FROM sellers
                    WHERE JSON_UNQUOTE(JSON_EXTRACT(embedding, '$.normalized_name')) = %s
                    LIMIT 1
                    """,
                    (normalized_name,),
                )
                row = await cur.fetchone()
                return SellerRepository._normalize_row(row) if row else None

    @staticmethod
    async def list_recent_sellers(limit: int = 100):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT id, cluster_id, seller_name, storefront_url, embedding, created_at
                    FROM sellers
                    ORDER BY id DESC
                    LIMIT %s
                    """,
                    (limit,),
                )
                rows = await cur.fetchall()
                return [SellerRepository._normalize_row(row) for row in rows]

    @staticmethod
    async def create_seller(
        seller_name: str,
        storefront_url: str | None,
        cluster_id: int | None,
        embedding: dict,
    ):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    INSERT INTO sellers (cluster_id, seller_name, storefront_url, embedding)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (cluster_id, seller_name, storefront_url, json.dumps(embedding)),
                )
                seller_id = cur.lastrowid

                await cur.execute(
                    """
                    SELECT id, cluster_id, seller_name, storefront_url, embedding, created_at
                    FROM sellers
                    WHERE id = %s
                    """,
                    (seller_id,),
                )
                return SellerRepository._normalize_row(await cur.fetchone())

    @staticmethod
    async def assign_cluster(seller_id: int, cluster_id: int):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE sellers SET cluster_id = %s WHERE id = %s",
                    (cluster_id, seller_id),
                )

    @staticmethod
    async def list_clusters_for_brand(brand_id: int):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT
                        sc.id AS cluster_id,
                        sc.cluster_name,
                        sc.risk_score,
                        s.id AS seller_id,
                        s.seller_name,
                        s.storefront_url,
                        s.embedding,
                        COUNT(DISTINCT v.id) AS open_violation_count
                    FROM seller_clusters sc
                    INNER JOIN sellers s ON s.cluster_id = sc.id
                    INNER JOIN listings l ON l.seller_id = s.id
                    INNER JOIN products p ON p.id = l.product_id
                    LEFT JOIN violations v ON v.listing_id = l.id AND v.status = 'open'
                    WHERE p.brand_id = %s
                    GROUP BY sc.id, sc.cluster_name, sc.risk_score, s.id, s.seller_name, s.storefront_url, s.embedding
                    ORDER BY open_violation_count DESC, sc.id, s.id
                    """,
                    (brand_id,),
                )
                rows = await cur.fetchall()

        clusters: dict[int, dict] = {}
        for row in rows:
            cluster_id = int(row["cluster_id"])
            if cluster_id not in clusters:
                clusters[cluster_id] = {
                    "cluster_id": cluster_id,
                    "cluster_name": row["cluster_name"],
                    "risk_score": float(row["risk_score"]) if row["risk_score"] is not None else None,
                    "open_violation_count": 0,
                    "sellers": [],
                }

            embedding = row.get("embedding")
            if isinstance(embedding, str):
                try:
                    embedding = json.loads(embedding)
                except json.JSONDecodeError:
                    embedding = None

            clusters[cluster_id]["sellers"].append(
                {
                    "seller_id": row["seller_id"],
                    "seller_name": row["seller_name"],
                    "storefront_url": row["storefront_url"],
                    "signature": embedding,
                    "open_violation_count": int(row["open_violation_count"] or 0),
                }
            )
            clusters[cluster_id]["open_violation_count"] += int(row["open_violation_count"] or 0)

        return list(clusters.values())


class SellerClusterRepository:
    @staticmethod
    async def create_cluster(cluster_name: str, risk_score: float | None = None) -> int:
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO seller_clusters (cluster_name, risk_score)
                    VALUES (%s, %s)
                    """,
                    (cluster_name, risk_score),
                )
                return int(cur.lastrowid)
