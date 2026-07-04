from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import require_auth
from app.repositories.violation_repository import ViolationRepository
from app.schemas.violations import ViolationResponse

router = APIRouter(prefix="/violations", tags=["violations"])


@router.get("/", response_model=list[ViolationResponse])
async def list_violations(current_user: dict = Depends(require_auth)):
    try:
        violations = await ViolationRepository.list_violations_for_brand(current_user["brand_id"])
        return violations
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
