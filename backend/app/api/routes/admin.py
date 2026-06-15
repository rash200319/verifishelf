from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import require_admin
from app.schemas.admin import AdminBrandOnboardRequest, AdminUserCreateRequest
from app.services.auth_service import AdminService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/onboard")
@router.post("/brands/onboard")
async def onboard_brand(payload: AdminBrandOnboardRequest, current_user: dict = Depends(require_admin)):
    try:
        brand = await AdminService.onboard_brand(payload.name, payload.plan.value)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "message": "Brand onboarded successfully",
        "brand": {
            "id": brand["id"],
            "name": brand["name"],
            "plan": brand["plan"],
            "torch_sub_id": brand["torch_sub_id"],
            "created_at": brand["created_at"],
        },
    }


@router.post("/users/create")
async def create_user(payload: AdminUserCreateRequest, current_user: dict = Depends(require_admin)):
    try:
        user = await AdminService.create_user(
            payload.brand_id,
            payload.full_name,
            payload.email,
            payload.password,
            payload.role,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "message": "User created successfully",
        "user": {
            "id": user["id"],
            "brand_id": user["brand_id"],
            "full_name": user["full_name"],
            "email": user["email"],
            "role": user["role"],
            "created_at": user["created_at"],
        },
    }
