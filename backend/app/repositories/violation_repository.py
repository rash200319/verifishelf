import aiomysql
from app.core import db

class ViolationRepository:
    @staticmethod
    async def get_open_violation_for_listing(listing_id: int):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")
        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT * FROM violations
                    WHERE listing_id = %s AND status = 'open'
                    LIMIT 1
                    """,
                    (listing_id,)
                )
                return await cur.fetchone()

    @staticmethod
    async def create_violation(
        listing_id: int,
        map_price: float,
        advertised_price: float,
        price_delta_pct: float | None = None,
        classifier_confidence: float | None = None,
        classifier_type: str | None = None,
    ):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")
        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    INSERT INTO violations (
                        listing_id,
                        map_price,
                        advertised_price,
                        price_delta_pct,
                        classifier_confidence,
                        classifier_type,
                        status
                    ) VALUES (%s, %s, %s, %s, %s, %s, 'open')
                    """,
                    (
                        listing_id,
                        map_price,
                        advertised_price,
                        price_delta_pct,
                        classifier_confidence,
                        classifier_type,
                    )
                )
        return await ViolationRepository.get_open_violation_for_listing(listing_id)

    @staticmethod
    async def update_violation_status(violation_id: int, status: str):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")
        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE violations SET status = %s WHERE id = %s",
                    (status, violation_id)
                )

    @staticmethod
    async def list_violations_for_brand(brand_id: int):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")
        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT 
                        v.id,
                        v.listing_id,
                        v.map_price,
                        v.advertised_price,
                        v.price_delta_pct,
                        v.classifier_confidence,
                        v.classifier_type,
                        v.status,
                        v.detected_at,
                        l.id as listing_id_val,
                        l.product_id,
                        l.seller_id,
                        l.marketplace_id,
                        l.listing_title,
                        l.listing_url,
                        l.image_url,
                        l.currency_code
                    FROM violations v
                    JOIN listings l ON v.listing_id = l.id
                    JOIN products p ON l.product_id = p.id
                    WHERE p.brand_id = %s
                    ORDER BY v.detected_at DESC
                    """,
                    (brand_id,)
                )
                rows = await cur.fetchall()
                
                violations = []
                for row in rows:
                    v_dict = {
                        "id": row["id"],
                        "listing_id": row["listing_id"],
                        "map_price": float(row["map_price"]),
                        "advertised_price": float(row["advertised_price"]),
                        "price_delta_pct": float(row["price_delta_pct"]) if row["price_delta_pct"] is not None else None,
                        "classifier_confidence": float(row["classifier_confidence"]) if row["classifier_confidence"] is not None else None,
                        "classifier_type": row["classifier_type"],
                        "status": row["status"],
                        "detected_at": row["detected_at"],
                        "listing": {
                            "id": row["listing_id_val"],
                            "product_id": row["product_id"],
                            "seller_id": row["seller_id"],
                            "marketplace_id": row["marketplace_id"],
                            "listing_title": row["listing_title"],
                            "listing_url": row["listing_url"],
                            "image_url": row["image_url"],
                            "currency_code": row["currency_code"]
                        }
                    }
                    violations.append(v_dict)
                return violations
