from datetime import date, datetime

from app.ml import inference
from app.ml.features import build_feature_row
from app.repositories.enforcement_letter_repository import EnforcementLetterRepository
from app.repositories.seller_repository import SellerRepository
from app.repositories.violation_repository import ViolationRepository
from app.services.alert_service import send_violation_alert
from app.services.promo_service import PromoService


class ViolationService:
    # Require sustained compliance before resolving -- a single crawl
    # observing advertised_price >= map_price (rounding noise, a momentary
    # scrape glitch) shouldn't flip status and risk an immediate
    # resolve-then-reopen on the very next crawl.
    CONSECUTIVE_COMPLIANT_THRESHOLD = 2

    # A violation dropping below MAP again this soon after resolving is
    # treated as the same ongoing issue reopening, not a new incident --
    # long enough to bridge normal crawl cadence and short-term price
    # flicker, short enough that a violation from a month ago recurring is
    # still its own new row.
    REOPEN_WINDOW_DAYS = 14

    @staticmethod
    def compute_severity(price_delta_pct: float) -> str:
        if price_delta_pct >= 20:
            return "high"
        if price_delta_pct >= 10:
            return "medium"
        return "low"

    @staticmethod
    def compute_price_delta_pct(map_price: float, advertised_price: float) -> float:
        if map_price <= 0:
            return 0.0
        return ((map_price - advertised_price) / map_price) * 100

    @classmethod
    async def _score_confidence(
        cls,
        *,
        price_delta_pct: float,
        listing_title: str,
        product_name: str,
        seller_id: int | None,
    ) -> tuple[float, str]:
        """
        Real classifier score when there's enough context to build a
        feature vector; falls back to the fixed heuristic confidence
        otherwise (no seller_id -- e.g. an older call site -- or the model
        artifact isn't available/errors).
        """
        if seller_id is None:
            return 0.99, "heuristic"

        seller = await SellerRepository.get_seller_by_id(seller_id)
        historical_count = await ViolationRepository.count_violations_for_seller(seller_id)
        reference_time = datetime.now()

        features = build_feature_row(
            price_delta_pct=price_delta_pct,
            listing_title=listing_title,
            product_name=product_name,
            seller_created_at=seller.get("created_at") if seller else None,
            reference_time=reference_time,
            seller_historical_violation_count=historical_count,
        )

        confidence = inference.predict_confidence(features)
        if confidence is None:
            return 0.99, "heuristic"
        return confidence, "xgboost_v1"

    @classmethod
    async def evaluate_listing_price(
        cls,
        *,
        brand_id: int,
        product_id: int,
        listing_id: int,
        map_price: float,
        advertised_price: float,
        marketplace_id: int,
        check_date: date | None = None,
        listing_title: str = "",
        product_name: str = "",
        seller_id: int | None = None,
    ) -> dict:
        resolved_date = check_date or date.today()
        existing_violation = await ViolationRepository.get_open_violation_for_listing(listing_id)

        is_compliant = advertised_price >= map_price
        is_allowed = False
        if not is_compliant:
            is_allowed = await PromoService.is_below_map_allowed(
                brand_id,
                product_id,
                marketplace_id,
                resolved_date,
            )

        if is_compliant or is_allowed:
            if not existing_violation:
                return {"action": "none" if is_compliant else "suppressed", "violation_id": None, "severity": None}

            streak = await ViolationRepository.bump_compliant_streak(existing_violation["id"])
            if streak < cls.CONSECUTIVE_COMPLIANT_THRESHOLD:
                return {
                    "action": "pending_resolution",
                    "violation_id": existing_violation["id"],
                    "severity": cls.compute_severity(float(existing_violation.get("price_delta_pct") or 0)),
                }

            await ViolationRepository.resolve_violation(existing_violation["id"])
            return {
                "action": "resolved" if is_compliant else "suppressed",
                "violation_id": existing_violation["id"],
                "severity": None,
            }

        if existing_violation:
            await ViolationRepository.reset_compliant_streak(existing_violation["id"])
            return {
                "action": "existing",
                "violation_id": existing_violation["id"],
                "severity": cls.compute_severity(float(existing_violation.get("price_delta_pct") or 0)),
            }

        price_delta_pct = cls.compute_price_delta_pct(map_price, advertised_price)
        classifier_confidence, classifier_type = await cls._score_confidence(
            price_delta_pct=price_delta_pct,
            listing_title=listing_title,
            product_name=product_name,
            seller_id=seller_id,
        )

        # A violation that resolved recently and has now dropped below MAP
        # again is the same ongoing issue reopening, not a fresh incident --
        # reopen that row instead of inserting an unrelated new one (see
        # REOPEN_WINDOW_DAYS).
        recent_resolved = await ViolationRepository.get_recently_resolved_violation(
            listing_id, within_days=cls.REOPEN_WINDOW_DAYS
        )
        if recent_resolved:
            violation = await ViolationRepository.reopen_violation(
                recent_resolved["id"],
                map_price=map_price,
                advertised_price=advertised_price,
                price_delta_pct=round(price_delta_pct, 2),
                classifier_confidence=round(classifier_confidence, 2),
                classifier_type=classifier_type,
            )
            action = "reopened"
        else:
            violation = await ViolationRepository.create_violation(
                listing_id=listing_id,
                map_price=map_price,
                advertised_price=advertised_price,
                price_delta_pct=round(price_delta_pct, 2),
                classifier_confidence=round(classifier_confidence, 2),
                classifier_type=classifier_type,
            )
            action = "created"

        if violation:
            # Best-effort -- a notification failure must never fail the
            # crawl or the violation record itself (see alert_service).
            try:
                context = await EnforcementLetterRepository.get_violation_context(violation["id"], brand_id)
                if context:
                    send_violation_alert(context)
            except Exception:
                pass

        return {
            "action": action,
            "violation_id": violation["id"] if violation else None,
            "severity": cls.compute_severity(price_delta_pct),
        }
