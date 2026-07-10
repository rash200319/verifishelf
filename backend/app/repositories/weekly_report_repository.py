import json
from datetime import date, datetime, timedelta

from aiomysql.cursors import DictCursor

from app.core import db


class WeeklyReportRepository:
    @staticmethod
    async def create_report(brand_id: int, start_date: date, end_date: date, report_content: dict):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        content_json = json.dumps(report_content, default=str)

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(
                    """
                    INSERT INTO weekly_reports (brand_id, report_start_date, report_end_date, report_content)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (brand_id, start_date, end_date, content_json),
                )
                report_id = cur.lastrowid

                await cur.execute(
                    """
                    SELECT id, brand_id, report_start_date, report_end_date, report_content, generated_at
                    FROM weekly_reports
                    WHERE id = %s
                    """,
                    (report_id,),
                )
                return await cur.fetchone()

    @staticmethod
    async def list_reports(brand_id: int, limit: int = 20):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT id, brand_id, report_start_date, report_end_date, report_content, generated_at
                    FROM weekly_reports
                    WHERE brand_id = %s
                    ORDER BY generated_at DESC
                    LIMIT %s
                    """,
                    (brand_id, limit),
                )
                return await cur.fetchall()

    @staticmethod
    async def get_report(report_id: int, brand_id: int):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT id, brand_id, report_start_date, report_end_date, report_content, generated_at
                    FROM weekly_reports
                    WHERE id = %s AND brand_id = %s
                    LIMIT 1
                    """,
                    (report_id, brand_id),
                )
                return await cur.fetchone()

    @staticmethod
    async def aggregate_brand_metrics(brand_id: int, start_date: date, end_date: date):
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        ninety_days_ago = end_dt - timedelta(days=90)

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT COUNT(DISTINCT l.id) AS listings_monitored
                    FROM listings l
                    INNER JOIN products p ON p.id = l.product_id
                    WHERE p.brand_id = %s
                      AND l.scraped_at BETWEEN %s AND %s
                    """,
                    (brand_id, start_dt, end_dt),
                )
                listings_monitored = int((await cur.fetchone())["listings_monitored"])

                await cur.execute(
                    """
                    SELECT COUNT(*) AS price_snapshots
                    FROM price_snapshots ps
                    INNER JOIN products p ON p.id = ps.product_id
                    WHERE p.brand_id = %s
                      AND ps.snapshot_time BETWEEN %s AND %s
                    """,
                    (brand_id, start_dt, end_dt),
                )
                price_snapshots = int((await cur.fetchone())["price_snapshots"])

                await cur.execute(
                    """
                    SELECT
                        COUNT(*) AS violations_detected,
                        SUM(CASE WHEN v.status = 'open' THEN 1 ELSE 0 END) AS violations_open
                    FROM violations v
                    INNER JOIN listings l ON l.id = v.listing_id
                    INNER JOIN products p ON p.id = l.product_id
                    WHERE p.brand_id = %s
                      AND v.detected_at BETWEEN %s AND %s
                    """,
                    (brand_id, start_dt, end_dt),
                )
                violation_row = await cur.fetchone()
                violations_detected = int(violation_row["violations_detected"] or 0)
                violations_open = int(violation_row["violations_open"] or 0)

                await cur.execute(
                    """
                    SELECT COUNT(*) AS active_promo_windows
                    FROM promo_windows
                    WHERE brand_id = %s
                      AND start_date <= %s
                      AND end_date >= %s
                    """,
                    (brand_id, end_date, start_date),
                )
                active_promo_windows = int((await cur.fetchone())["active_promo_windows"])

                await cur.execute(
                    """
                    SELECT
                        p.id AS product_id,
                        p.name AS product_name,
                        p.map_price,
                        COUNT(ps.id) AS snapshot_count,
                        AVG(ps.price) AS avg_observed_price,
                        (
                            SELECT ps2.price
                            FROM price_snapshots ps2
                            WHERE ps2.product_id = p.id
                              AND ps2.snapshot_time BETWEEN %s AND %s
                            ORDER BY ps2.snapshot_time DESC
                            LIMIT 1
                        ) AS latest_price,
                        (
                            SELECT ps3.price
                            FROM price_snapshots ps3
                            WHERE ps3.product_id = p.id
                              AND ps3.snapshot_time >= %s
                            ORDER BY ps3.snapshot_time ASC
                            LIMIT 1
                        ) AS price_90d_start,
                        (
                            SELECT ps4.price
                            FROM price_snapshots ps4
                            WHERE ps4.product_id = p.id
                              AND ps4.snapshot_time >= %s
                            ORDER BY ps4.snapshot_time DESC
                            LIMIT 1
                        ) AS price_90d_end
                    FROM products p
                    LEFT JOIN price_snapshots ps
                        ON ps.product_id = p.id
                       AND ps.snapshot_time BETWEEN %s AND %s
                    WHERE p.brand_id = %s
                    GROUP BY p.id, p.name, p.map_price
                    ORDER BY p.id
                    """,
                    (start_dt, end_dt, ninety_days_ago, ninety_days_ago, start_dt, end_dt, brand_id),
                )
                products = await cur.fetchall()

                await cur.execute(
                    """
                    SELECT
                        s.id AS seller_id,
                        s.seller_name,
                        COUNT(*) AS violation_count,
                        (
                            SELECT l2.listing_url
                            FROM violations v2
                            INNER JOIN listings l2 ON l2.id = v2.listing_id
                            WHERE l2.seller_id = s.id
                              AND v2.detected_at BETWEEN %s AND %s
                            ORDER BY v2.detected_at DESC
                            LIMIT 1
                        ) AS listing_url
                    FROM violations v
                    INNER JOIN listings l ON l.id = v.listing_id
                    INNER JOIN products p ON p.id = l.product_id
                    INNER JOIN sellers s ON s.id = l.seller_id
                    WHERE p.brand_id = %s
                      AND v.detected_at BETWEEN %s AND %s
                    GROUP BY s.id, s.seller_name
                    ORDER BY violation_count DESC
                    LIMIT 5
                    """,
                    (start_dt, end_dt, brand_id, start_dt, end_dt),
                )
                top_offending_sellers = await cur.fetchall()

                # "Repeat offender" = a seller violating this brand's MAP more
                # than once ever (all-time, not scoped to the report period) --
                # the whole point is flagging sellers who keep coming back.
                await cur.execute(
                    """
                    SELECT COUNT(*) AS repeat_offenders
                    FROM (
                        SELECT s.id
                        FROM violations v
                        INNER JOIN listings l ON l.id = v.listing_id
                        INNER JOIN products p ON p.id = l.product_id
                        INNER JOIN sellers s ON s.id = l.seller_id
                        WHERE p.brand_id = %s
                        GROUP BY s.id
                        HAVING COUNT(*) > 1
                    ) AS repeat_sellers
                    """,
                    (brand_id,),
                )
                repeat_offenders = int((await cur.fetchone())["repeat_offenders"])

        return {
            "summary": {
                "listings_monitored": listings_monitored,
                "price_snapshots": price_snapshots,
                "violations_detected": violations_detected,
                "violations_open": violations_open,
                "active_promo_windows": active_promo_windows,
                "repeat_offenders": repeat_offenders,
            },
            "products": products,
            "top_offending_sellers": top_offending_sellers,
        }
