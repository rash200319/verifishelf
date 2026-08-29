from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import db
from app.models import WeeklyReport


class WeeklyReportRepository:
    _FIELDS = [
        "id",
        "brand_id",
        "report_start_date",
        "report_end_date",
        "report_content",
        "generated_at",
    ]

    @staticmethod
    async def create_report(
        brand_id: int,
        start_date: date,
        end_date: date,
        report_content: dict,
        session: AsyncSession | None = None,
    ):
        content_json = json.dumps(report_content, default=str)
        async with db.session_scope(session) as s:
            report = WeeklyReport(
                brand_id=brand_id,
                report_start_date=start_date,
                report_end_date=end_date,
                report_content=content_json,
            )
            s.add(report)
            await s.flush()
            await s.refresh(report)
            return db.model_to_dict(report, WeeklyReportRepository._FIELDS)

    @staticmethod
    async def list_reports(brand_id: int, limit: int = 20, session: AsyncSession | None = None):
        async with db.session_scope(session) as s:
            stmt = (
                select(WeeklyReport)
                .where(WeeklyReport.brand_id == brand_id)
                .order_by(WeeklyReport.generated_at.desc())
                .limit(limit)
            )
            rows = (await s.execute(stmt)).scalars().all()
            return [db.model_to_dict(row, WeeklyReportRepository._FIELDS) for row in rows]

    @staticmethod
    async def get_report(report_id: int, brand_id: int, session: AsyncSession | None = None):
        async with db.session_scope(session) as s:
            stmt = (
                select(WeeklyReport)
                .where(WeeklyReport.id == report_id, WeeklyReport.brand_id == brand_id)
                .limit(1)
            )
            row = (await s.execute(stmt)).scalar_one_or_none()
            return db.model_to_dict(row, WeeklyReportRepository._FIELDS)

    @staticmethod
    async def aggregate_brand_metrics(
        brand_id: int,
        start_date: date,
        end_date: date,
        session: AsyncSession | None = None,
    ):
        start_dt = datetime.combine(start_date, datetime.min.time())
        end_dt = datetime.combine(end_date, datetime.max.time())
        ninety_days_ago = end_dt - timedelta(days=90)

        async with db.session_scope(session) as s:
            listings_monitored = int(
                (
                    await s.execute(
                        text(
                            """
                            SELECT COUNT(DISTINCT l.id) AS listings_monitored
                            FROM listings l
                            INNER JOIN products p ON p.id = l.product_id
                            WHERE p.brand_id = :brand_id
                              AND l.scraped_at BETWEEN :start_dt AND :end_dt
                            """
                        ),
                        {"brand_id": brand_id, "start_dt": start_dt, "end_dt": end_dt},
                    )
                ).mappings().one()["listings_monitored"]
            )

            price_snapshots = int(
                (
                    await s.execute(
                        text(
                            """
                            SELECT COUNT(*) AS price_snapshots
                            FROM price_snapshots ps
                            INNER JOIN products p ON p.id = ps.product_id
                            WHERE p.brand_id = :brand_id
                              AND ps.snapshot_time BETWEEN :start_dt AND :end_dt
                            """
                        ),
                        {"brand_id": brand_id, "start_dt": start_dt, "end_dt": end_dt},
                    )
                ).mappings().one()["price_snapshots"]
            )

            violation_row = (
                await s.execute(
                    text(
                        """
                        SELECT
                            COUNT(*) AS violations_detected,
                            SUM(CASE WHEN v.status = 'open' THEN 1 ELSE 0 END) AS violations_open
                        FROM violations v
                        INNER JOIN listings l ON l.id = v.listing_id
                        INNER JOIN products p ON p.id = l.product_id
                        WHERE p.brand_id = :brand_id
                          AND v.detected_at BETWEEN :start_dt AND :end_dt
                        """
                    ),
                    {"brand_id": brand_id, "start_dt": start_dt, "end_dt": end_dt},
                )
            ).mappings().one()
            violations_detected = int(violation_row["violations_detected"] or 0)
            violations_open = int(violation_row["violations_open"] or 0)

            active_promo_windows = int(
                (
                    await s.execute(
                        text(
                            """
                            SELECT COUNT(*) AS active_promo_windows
                            FROM promo_windows
                            WHERE brand_id = :brand_id
                              AND start_date <= :end_date
                              AND end_date >= :start_date
                            """
                        ),
                        {"brand_id": brand_id, "end_date": end_date, "start_date": start_date},
                    )
                ).mappings().one()["active_promo_windows"]
            )

            products = (
                await s.execute(
                    text(
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
                                  AND ps2.snapshot_time BETWEEN :start_dt AND :end_dt
                                ORDER BY ps2.snapshot_time DESC
                                LIMIT 1
                            ) AS latest_price,
                            (
                                SELECT ps3.price
                                FROM price_snapshots ps3
                                WHERE ps3.product_id = p.id
                                  AND ps3.snapshot_time >= :ninety_days_ago
                                ORDER BY ps3.snapshot_time ASC
                                LIMIT 1
                            ) AS price_90d_start,
                            (
                                SELECT ps4.price
                                FROM price_snapshots ps4
                                WHERE ps4.product_id = p.id
                                  AND ps4.snapshot_time >= :ninety_days_ago
                                ORDER BY ps4.snapshot_time DESC
                                LIMIT 1
                            ) AS price_90d_end
                        FROM products p
                        LEFT JOIN price_snapshots ps
                            ON ps.product_id = p.id
                           AND ps.snapshot_time BETWEEN :start_dt AND :end_dt
                        WHERE p.brand_id = :brand_id
                        GROUP BY p.id, p.name, p.map_price
                        ORDER BY p.id
                        """
                    ),
                    {
                        "brand_id": brand_id,
                        "start_dt": start_dt,
                        "end_dt": end_dt,
                        "ninety_days_ago": ninety_days_ago,
                    },
                )
            ).mappings().all()

            top_offending_sellers = (
                await s.execute(
                    text(
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
                                  AND v2.detected_at BETWEEN :start_dt AND :end_dt
                                ORDER BY v2.detected_at DESC
                                LIMIT 1
                            ) AS listing_url
                        FROM violations v
                        INNER JOIN listings l ON l.id = v.listing_id
                        INNER JOIN products p ON p.id = l.product_id
                        INNER JOIN sellers s ON s.id = l.seller_id
                        WHERE p.brand_id = :brand_id
                          AND v.detected_at BETWEEN :start_dt AND :end_dt
                        GROUP BY s.id, s.seller_name
                        ORDER BY violation_count DESC
                        LIMIT 5
                        """
                    ),
                    {"brand_id": brand_id, "start_dt": start_dt, "end_dt": end_dt},
                )
            ).mappings().all()

            repeat_offenders = int(
                (
                    await s.execute(
                        text(
                            """
                            SELECT COUNT(*) AS repeat_offenders
                            FROM (
                                SELECT s.id
                                FROM violations v
                                INNER JOIN listings l ON l.id = v.listing_id
                                INNER JOIN products p ON p.id = l.product_id
                                INNER JOIN sellers s ON s.id = l.seller_id
                                WHERE p.brand_id = :brand_id
                                GROUP BY s.id
                                HAVING COUNT(*) > 1
                            ) AS repeat_sellers
                            """
                        ),
                        {"brand_id": brand_id},
                    )
                ).mappings().one()["repeat_offenders"]
            )

        return {
            "summary": {
                "listings_monitored": listings_monitored,
                "price_snapshots": price_snapshots,
                "violations_detected": violations_detected,
                "violations_open": violations_open,
                "active_promo_windows": active_promo_windows,
                "repeat_offenders": repeat_offenders,
            },
            "products": [dict(row) for row in products],
            "top_offending_sellers": [dict(row) for row in top_offending_sellers],
        }
