from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import require_auth, require_brand_admin
from app.schemas.violations import EnforcementGenerateRequest, EnforcementLetterResponse
from app.services.enforcement_service import EnforcementService

router = APIRouter(prefix="/enforcement", tags=["enforcement"])


def _format_letter(letter: dict) -> EnforcementLetterResponse:
    return EnforcementLetterResponse(
        id=letter["id"],
        violation_id=letter["violation_id"],
        letter_content=letter["letter_content"],
        generated_by=letter["generated_by"],
        screenshot_base64=letter.get("screenshot_base64"),
        generated_at=letter["generated_at"],
    )


@router.post("/violations/{violation_id}", response_model=EnforcementLetterResponse)
async def generate_enforcement_letter(
    violation_id: int,
    payload: EnforcementGenerateRequest | None = None,
    current_user: dict = Depends(require_brand_admin),
):
    # Admin-only: this drafts (and is the basis for sending) a formal
    # notice in the brand's name to a third party -- an external-facing,
    # reputational action that shouldn't be initiated by any analyst
    # without sign-off.
    request = payload or EnforcementGenerateRequest()
    try:
        letter = await EnforcementService.generate_for_violation(
            violation_id,
            current_user["brand_id"],
            provider=request.provider,
            force_regenerate=request.force_regenerate,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return _format_letter(letter)


@router.get("/violations/{violation_id}", response_model=EnforcementLetterResponse)
async def get_enforcement_letter(violation_id: int, current_user: dict = Depends(require_auth)):
    try:
        letter = await EnforcementService.get_for_violation(violation_id, current_user["brand_id"])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if letter is None:
        raise HTTPException(status_code=404, detail="Enforcement letter not found")

    return _format_letter(letter)
