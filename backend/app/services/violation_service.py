from datetime import date

from app.repositories.violation_repository import ViolationRepository
from app.services.promo_service import PromoService


class ViolationService:
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
    ) -> dict:
        resolved_date = check_date or date.today()
        existing_violation = await ViolationRepository.get_open_violation_for_listing(listing_id)

        if advertised_price >= map_price:
            if existing_violation:
                await ViolationRepository.update_violation_status(existing_violation["id"], "resolved")
                return {"action": "resolved", "violation_id": existing_violation["id"], "severity": None}

            return {"action": "none", "violation_id": None, "severity": None}

        is_allowed = await PromoService.is_below_map_allowed(
            brand_id,
            product_id,
            marketplace_id,
            resolved_date,
        )
        if is_allowed:
            if existing_violation:
                await ViolationRepository.update_violation_status(existing_violation["id"], "resolved")
                return {"action": "suppressed", "violation_id": existing_violation["id"], "severity": None}

            return {"action": "suppressed", "violation_id": None, "severity": None}

        if existing_violation:
            return {
                "action": "existing",
                "violation_id": existing_violation["id"],
                "severity": cls.compute_severity(float(existing_violation.get("price_delta_pct") or 0)),
            }

        price_delta_pct = cls.compute_price_delta_pct(map_price, advertised_price)
        violation = await ViolationRepository.create_violation(
            listing_id=listing_id,
            map_price=map_price,
            advertised_price=advertised_price,
            price_delta_pct=price_delta_pct,
            classifier_confidence=0.99,
            classifier_type="heuristic",
        )

        return {
            "action": "created",
            "violation_id": violation["id"] if violation else None,
            "severity": cls.compute_severity(price_delta_pct),
        }
