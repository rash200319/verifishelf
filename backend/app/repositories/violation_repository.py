from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import db
from app.models import Listing, Product, Seller, Violation


class ViolationRepository:
    @staticmethod
    async def get_open_violation_for_listing(listing_id: int, session: AsyncSession | None = None):
        async with db.session_scope(session) as s:
            stmt = (
                select(Violation)
                .where(Violation.listing_id == listing_id, Violation.status == "open")
                .limit(1)
            )
            row = (await s.execute(stmt)).scalar_one_or_none()
            return db.model_to_dict(row)

    @staticmethod
    async def create_violation(
        listing_id: int,
        map_price: float,
        advertised_price: float,
        price_delta_pct: float | None = None,
        classifier_confidence: float | None = None,
        classifier_type: str | None = None,
        session: AsyncSession | None = None,
    ):
        async with db.session_scope(session) as s:
            violation = Violation(
                listing_id=listing_id,
                map_price=map_price,
                advertised_price=advertised_price,
                price_delta_pct=price_delta_pct,
                classifier_confidence=classifier_confidence,
                classifier_type=classifier_type,
                status="open",
            )
            s.add(violation)
            await s.flush()
            return await ViolationRepository.get_open_violation_for_listing(listing_id, session=s)

    @staticmethod
    async def get_recently_resolved_violation(
        listing_id: int,
        within_days: int,
        session: AsyncSession | None = None,
    ):
        async with db.session_scope(session) as s:
            stmt = text(
                """
                SELECT * FROM violations
                WHERE listing_id = :listing_id
                  AND status = 'resolved'
                  AND resolved_at >= DATE_SUB(NOW(), INTERVAL :within_days DAY)
                ORDER BY resolved_at DESC
                LIMIT 1
                """
            )
            result = await s.execute(stmt, {"listing_id": listing_id, "within_days": within_days})
            row = result.mappings().first()
            return dict(row) if row else None

    @staticmethod
    async def reopen_violation(
        violation_id: int,
        map_price: float,
        advertised_price: float,
        price_delta_pct: float | None,
        classifier_confidence: float | None,
        classifier_type: str | None,
        session: AsyncSession | None = None,
    ):
        async with db.session_scope(session) as s:
            violation = await s.get(Violation, violation_id)
            if violation is None:
                return None
            violation.status = "open"
            violation.resolved_at = None
            violation.last_detected_at = datetime.utcnow()
            violation.reopened_count = int(violation.reopened_count or 0) + 1
            violation.consecutive_compliant_checks = 0
            violation.map_price = map_price
            violation.advertised_price = advertised_price
            violation.price_delta_pct = price_delta_pct
            violation.classifier_confidence = classifier_confidence
            violation.classifier_type = classifier_type
            await s.flush()
            await s.refresh(violation)
            return db.model_to_dict(violation)

    @staticmethod
    async def resolve_violation(violation_id: int, session: AsyncSession | None = None):
        async with db.session_scope(session) as s:
            violation = await s.get(Violation, violation_id)
            if violation is None:
                return
            violation.status = "resolved"
            violation.resolved_at = datetime.utcnow()
            await s.flush()

    @staticmethod
    async def bump_compliant_streak(violation_id: int, session: AsyncSession | None = None) -> int:
        async with db.session_scope(session) as s:
            violation = await s.get(Violation, violation_id)
            if violation is None:
                return 0
            violation.consecutive_compliant_checks = int(violation.consecutive_compliant_checks or 0) + 1
            await s.flush()
            return int(violation.consecutive_compliant_checks)

    @staticmethod
    async def reset_compliant_streak(violation_id: int, session: AsyncSession | None = None):
        async with db.session_scope(session) as s:
            violation = await s.get(Violation, violation_id)
            if violation is None:
                return
            if int(violation.consecutive_compliant_checks or 0) != 0:
                violation.consecutive_compliant_checks = 0
                await s.flush()

    @staticmethod
    async def count_violations_for_seller(seller_id: int, session: AsyncSession | None = None) -> int:
        async with db.session_scope(session) as s:
            stmt = (
                select(func.count())
                .select_from(Violation)
                .join(Listing, Violation.listing_id == Listing.id)
                .where(Listing.seller_id == seller_id)
            )
            return int((await s.execute(stmt)).scalar_one() or 0)

    @staticmethod
    async def list_violations_for_brand(
        brand_id: int,
        limit: int = 300,
        session: AsyncSession | None = None,
    ):
        async with db.session_scope(session) as s:
            stmt = (
                select(
                    Violation.id,
                    Violation.listing_id,
                    Violation.map_price,
                    Violation.advertised_price,
                    Violation.price_delta_pct,
                    Violation.classifier_confidence,
                    Violation.classifier_type,
                    Violation.status,
                    Violation.detected_at,
                    Violation.last_detected_at,
                    Violation.reopened_count,
                    Listing.id.label("listing_id_val"),
                    Listing.product_id,
                    Listing.seller_id,
                    Listing.marketplace_id,
                    Listing.listing_title,
                    Listing.listing_url,
                    Listing.image_url,
                    Listing.currency_code,
                    Seller.seller_name,
                    Product.name.label("product_name"),
                )
                .join(Listing, Violation.listing_id == Listing.id)
                .join(Product, Listing.product_id == Product.id)
                .join(Seller, Listing.seller_id == Seller.id)
                .where(Product.brand_id == brand_id)
                .order_by(Violation.last_detected_at.desc())
                .limit(limit)
            )
            rows = (await s.execute(stmt)).mappings().all()

            violations = []
            for row in rows:
                violations.append(
                    {
                        "id": row["id"],
                        "listing_id": row["listing_id"],
                        "map_price": float(row["map_price"]),
                        "advertised_price": float(row["advertised_price"]),
                        "price_delta_pct": float(row["price_delta_pct"])
                        if row["price_delta_pct"] is not None
                        else None,
                        "classifier_confidence": float(row["classifier_confidence"])
                        if row["classifier_confidence"] is not None
                        else None,
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
                        },
                    }
                )
            return violations
