from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import require_admin
from app.schemas.admin import AdminBrandOnboardRequest, AdminUserCreateRequest, BrandReviewRequest
from app.services.auth_service import AdminService, ReviewService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/brands/pending")
async def list_pending_brands(current_user: dict = Depends(require_admin)):
    try:
        brands = await ReviewService.list_pending_brands()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"brands": brands}


@router.post("/brands/{brand_id}/approve")
async def approve_brand(brand_id: int, payload: BrandReviewRequest, current_user: dict = Depends(require_admin)):
    try:
        brand = await ReviewService.approve_brand(brand_id, payload.reviewed_by, payload.review_notes)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")

    return {"message": "Brand approved successfully", "brand": brand}


@router.post("/brands/{brand_id}/reject")
async def reject_brand(brand_id: int, payload: BrandReviewRequest, current_user: dict = Depends(require_admin)):
    try:
        brand = await ReviewService.reject_brand(brand_id, payload.reviewed_by, payload.review_notes)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")

    return {"message": "Brand rejected successfully", "brand": brand}


@router.post("/brands/{brand_id}/request-info")
async def request_brand_info(brand_id: int, payload: BrandReviewRequest, current_user: dict = Depends(require_admin)):
    try:
        brand = await ReviewService.request_more_info(brand_id, payload.reviewed_by, payload.review_notes)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")

    return {"message": "Brand marked as needs more info", "brand": brand}


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
            "status": brand["status"],
            "company_name": brand["company_name"],
            "business_url": brand["business_url"],
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
