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
    async def get_recently_resolved_violation(listing_id: int, within_days: int):
        """Most recently resolved violation for this listing if it resolved
        within the last `within_days` days -- the candidate to reopen
        instead of inserting an unrelated new row."""
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")
        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT * FROM violations
                    WHERE listing_id = %s
                      AND status = 'resolved'
                      AND resolved_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
                    ORDER BY resolved_at DESC
                    LIMIT 1
                    """,
                    (listing_id, within_days),
                )
                return await cur.fetchone()

    @staticmethod
    async def reopen_violation(
        violation_id: int,
        map_price: float,
        advertised_price: float,
        price_delta_pct: float | None,
        classifier_confidence: float | None,
        classifier_type: str | None,
    ):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")
        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    UPDATE violations
                    SET status = 'open',
                        resolved_at = NULL,
                        last_detected_at = CURRENT_TIMESTAMP,
                        reopened_count = reopened_count + 1,
                        consecutive_compliant_checks = 0,
                        map_price = %s,
                        advertised_price = %s,
                        price_delta_pct = %s,
                        classifier_confidence = %s,
                        classifier_type = %s
                    WHERE id = %s
                    """,
                    (
                        map_price,
                        advertised_price,
                        price_delta_pct,
                        classifier_confidence,
                        classifier_type,
                        violation_id,
                    ),
                )
                await cur.execute("SELECT * FROM violations WHERE id = %s", (violation_id,))
                return await cur.fetchone()

    @staticmethod
    async def resolve_violation(violation_id: int):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")
        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    """
                    UPDATE violations
                    SET status = 'resolved', resolved_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (violation_id,),
                )

    @staticmethod
    async def bump_compliant_streak(violation_id: int) -> int:
        """Increment the consecutive-compliant-checks counter and return the
        new value, so the caller can decide whether it's crossed the
        resolve threshold yet."""
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")
        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    "UPDATE violations SET consecutive_compliant_checks = consecutive_compliant_checks + 1 WHERE id = %s",
                    (violation_id,),
                )
                await cur.execute(
                    "SELECT consecutive_compliant_checks FROM violations WHERE id = %s",
                    (violation_id,),
                )
                row = await cur.fetchone()
                return int(row["consecutive_compliant_checks"]) if row else 0

    @staticmethod
    async def reset_compliant_streak(violation_id: int):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")
        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "UPDATE violations SET consecutive_compliant_checks = 0 WHERE id = %s AND consecutive_compliant_checks != 0",
                    (violation_id,),
                )

    @staticmethod
    async def count_violations_for_seller(seller_id: int) -> int:
        """
        Count of this seller's prior violations (any status), across all
        their listings -- used as a real-time feature for the ML classifier
        (a repeat offender scores differently than a first-time flag).
        """
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")
        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT COUNT(*) AS violation_count
                    FROM violations v
                    JOIN listings l ON v.listing_id = l.id
                    WHERE l.seller_id = %s
                    """,
                    (seller_id,),
                )
                row = await cur.fetchone()
                return int(row["violation_count"]) if row else 0

    @staticmethod
    async def list_violations_for_brand(brand_id: int, limit: int = 300):
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
                        v.last_detected_at,
                        v.reopened_count,
                        l.id as listing_id_val,
                        l.product_id,
                        l.seller_id,
                        l.marketplace_id,
                        l.listing_title,
                        l.listing_url,
                        l.image_url,
                        l.currency_code,
                        s.seller_name,
                        p.name as product_name
                    FROM violations v
                    JOIN listings l ON v.listing_id = l.id
                    JOIN products p ON l.product_id = p.id
                    JOIN sellers s ON l.seller_id = s.id
                    WHERE p.brand_id = %s
                    ORDER BY v.last_detected_at DESC
                    LIMIT %s
                    """,
                    (brand_id, limit)
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
                        "last_detected_at": row["last_detected_at"],
                        "reopened_count": row["reopened_count"],
                        "listing": {
                            "id": row["listing_id_val"],
                            "product_id": row["product_id"],
                            "seller_id": row["seller_id"],
                            "marketplace_id": row["marketplace_id"],
                            "listing_title": row["listing_title"],
                            "listing_url": row["listing_url"],
                            "image_url": row["image_url"],
                            "currency_code": row["currency_code"],
                            "seller_name": row["seller_name"],
                            "product_name": row["product_name"],
                        }
                    }
                    violations.append(v_dict)
                return violations
