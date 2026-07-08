from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import require_auth
from app.repositories.violation_repository import ViolationRepository
from app.schemas.violations import ViolationResponse
from app.services.violation_service import ViolationService

router = APIRouter(prefix="/violations", tags=["violations"])


def _format_violation(violation: dict) -> ViolationResponse:
    severity = None
    if violation.get("price_delta_pct") is not None and violation.get("status") == "open":
        severity = ViolationService.compute_severity(float(violation["price_delta_pct"]))

    return ViolationResponse(
        id=violation["id"],
        listing_id=violation["listing_id"],
        map_price=violation["map_price"],
        advertised_price=violation["advertised_price"],
        price_delta_pct=violation.get("price_delta_pct"),
        classifier_confidence=violation.get("classifier_confidence"),
        classifier_type=violation.get("classifier_type"),
        status=violation["status"],
        severity=severity,
        detected_at=violation["detected_at"],
        listing=violation.get("listing"),
    )


@router.get("/", response_model=list[ViolationResponse])
async def list_violations(current_user: dict = Depends(require_auth)):
    try:
        violations = await ViolationRepository.list_violations_for_brand(current_user["brand_id"])
        return [_format_violation(violation) for violation in violations]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
