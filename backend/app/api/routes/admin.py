from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import require_admin, require_brand_admin, require_auth
from app.schemas.admin import AdminBrandOnboardRequest, AdminUserCreateRequest, BrandReviewRequest
from app.services.auth_service import AdminService, ReviewService

router = APIRouter(prefix="/admin", tags=["admin"])

# =====================================================
# TORCHPROXY ADMIN ROUTES (Super-admin functions)
# Require special TorchProxy admin key
# =====================================================

@router.get("/torchproxy/brands/pending")
async def list_pending_brands(current_user: dict = Depends(require_admin)):
    """List pending brand registrations (TorchProxy admin only)"""
    try:
        brands = await ReviewService.list_pending_brands()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {"brands": brands}


@router.post("/torchproxy/brands/{brand_id}/approve")
async def approve_brand(brand_id: int, payload: BrandReviewRequest, current_user: dict = Depends(require_admin)):
    """Approve a pending brand (TorchProxy admin only)"""
    try:
        brand = await ReviewService.approve_brand(brand_id, payload.reviewed_by, payload.review_notes)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")

    return {"message": "Brand approved successfully", "brand": brand}


@router.post("/torchproxy/brands/{brand_id}/reject")
async def reject_brand(brand_id: int, payload: BrandReviewRequest, current_user: dict = Depends(require_admin)):
    """Reject a pending brand (TorchProxy admin only)"""
    try:
        brand = await ReviewService.reject_brand(brand_id, payload.reviewed_by, payload.review_notes)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")

    return {"message": "Brand rejected successfully", "brand": brand}


@router.post("/torchproxy/brands/{brand_id}/request-info")
async def request_brand_info(brand_id: int, payload: BrandReviewRequest, current_user: dict = Depends(require_admin)):
    """Request more info from a pending brand (TorchProxy admin only)"""
    try:
        brand = await ReviewService.request_more_info(brand_id, payload.reviewed_by, payload.review_notes)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if brand is None:
        raise HTTPException(status_code=404, detail="Brand not found")

    return {"message": "Brand marked as needs more info", "brand": brand}


@router.post("/torchproxy/onboard")
@router.post("/torchproxy/brands/onboard")
async def onboard_brand(payload: AdminBrandOnboardRequest, current_user: dict = Depends(require_admin)):
    """Onboard a new brand (TorchProxy admin only)"""
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


# =====================================================
# BRAND ADMIN ROUTES (Brand-level admin functions)
# Require brand admin role within approved brand
# =====================================================

@router.post("/onboard-my-brand")
async def onboard_my_brand(payload: AdminBrandOnboardRequest, current_user: dict = Depends(require_brand_admin)):
    """Brand admins can complete onboarding for their brand (Brand admin only)"""
    # Brand admins can only onboard their own brand
    if payload.name != current_user["brand_name"]:
        raise HTTPException(status_code=403, detail="Brand name must match your current brand")
    
    try:
        # Update the existing brand's plan and torch sub-id
        from app.repositories.brand_repository import BrandRepository
        brand = await BrandRepository.update_brand_plan(
            current_user["brand_id"],
            payload.plan.value,
            f"torch_{current_user['brand_id']}"
        )
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
async def create_user(payload: AdminUserCreateRequest, current_user: dict = Depends(require_brand_admin)):
    """Create a user for the brand (Brand admin only)"""
    # Brand admins can only create users for their own brand
    if payload.brand_id != current_user["brand_id"]:
        raise HTTPException(status_code=403, detail="Can only create users for your own brand")
    
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


# =====================================================
# LEGACY ROUTES (For backward compatibility)
# These will be deprecated in favor of the separated routes above
# =====================================================

@router.get("/brands/pending")
async def list_pending_brands_legacy(current_user: dict = Depends(require_admin)):
    """Legacy endpoint - use /torchproxy/brands/pending instead"""
    return await list_pending_brands(current_user)


@router.post("/brands/{brand_id}/approve")
async def approve_brand_legacy(brand_id: int, payload: BrandReviewRequest, current_user: dict = Depends(require_admin)):
    """Legacy endpoint - use /torchproxy/brands/{brand_id}/approve instead"""
    return await approve_brand(brand_id, payload, current_user)


@router.post("/brands/{brand_id}/reject")
async def reject_brand_legacy(brand_id: int, payload: BrandReviewRequest, current_user: dict = Depends(require_admin)):
    """Legacy endpoint - use /torchproxy/brands/{brand_id}/reject instead"""
    return await reject_brand(brand_id, payload, current_user)


@router.post("/brands/{brand_id}/request-info")
async def request_brand_info_legacy(brand_id: int, payload: BrandReviewRequest, current_user: dict = Depends(require_admin)):
    """Legacy endpoint - use /torchproxy/brands/{brand_id}/request-info instead"""
    return await request_brand_info(brand_id, payload, current_user)


@router.post("/onboard")
@router.post("/brands/onboard")
async def onboard_brand_legacy(payload: AdminBrandOnboardRequest, current_user: dict = Depends(require_admin)):
    """Legacy endpoint - use /torchproxy/onboard instead"""
    return await onboard_brand(payload, current_user)
