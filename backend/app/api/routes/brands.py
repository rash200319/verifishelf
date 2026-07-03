from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import require_brand_admin
from app.schemas.invites import BrandInviteCreateRequest, BrandInviteListResponse, BrandInviteResponse
from app.services.auth_service import InviteAdminService

router = APIRouter(prefix="/brands", tags=["brands"])


@router.get("/invites", response_model=BrandInviteListResponse)
async def list_invites(current_user: dict = Depends(require_brand_admin)):
    try:
        invites = await InviteAdminService.list_invites(int(current_user["brand_id"]))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"invites": invites}


@router.post("/invites", response_model=BrandInviteResponse)
async def create_invite(payload: BrandInviteCreateRequest, current_user: dict = Depends(require_brand_admin)):
    try:
        result = await InviteAdminService.create_invite(
            int(current_user["brand_id"]),
            email=payload.email,
            role=payload.role,
            expires_in_minutes=payload.expires_in_minutes,
            created_by=int(current_user["user_id"]),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if result is None:
        raise HTTPException(status_code=400, detail="Unable to create invite")

    return {
        "message": "Invite created successfully",
        "invite": {
            **result["invite"],
            "invite_code": result["invite_code"],
        },
    }
