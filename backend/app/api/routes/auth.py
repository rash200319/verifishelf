from fastapi import APIRouter, HTTPException

from app.core.auth import create_access_token
from app.schemas.auth import (
    BrandRegisterRequest,
    BrandRegisterResponse,
    InviteJoinResponse,
    JoinInviteRequest,
    LoginRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def _strip_password_hash(user: dict) -> dict:
    return {k: v for k, v in user.items() if k != "password_hash"}


@router.post("/register", response_model=BrandRegisterResponse)
async def register_brand_owner(payload: BrandRegisterRequest):
    try:
        result = await AuthService.register_brand_owner(
            payload.full_name,
            payload.email,
            payload.password,
            payload.brand_name,
            payload.business_url,
            payload.company_name,
            payload.notes,
            registration_number=payload.registration_number,
            business_address=payload.business_address,
            industry=payload.industry,
            contact_title=payload.contact_title,
            contact_phone=payload.contact_phone,
            estimated_sku_range=payload.estimated_sku_range,
            current_marketplaces=payload.current_marketplaces,
            authorized_attestation=payload.authorized_attestation,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "message": "Brand registration submitted for review",
        "brand": result["brand"],
        "user": _strip_password_hash(result["user"]),
    }


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    session = await AuthService.login(payload.email, payload.password)
    if session is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials or brand is not approved yet",
        )

    user = session["user"]
    brand = session["brand"]  # None for a superadmin -- not scoped to any brand
    token = create_access_token(
        {
            "sub": user["email"],
            "user_id": user["id"],
            "brand_id": brand["id"] if brand else None,
            "brand_name": brand["name"] if brand else None,
            "brand_status": brand["status"] if brand else None,
            "role": user["role"],
            "email": user["email"],
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user["id"],
        "brand_id": brand["id"] if brand else None,
        "brand_name": brand["name"] if brand else None,
        "role": user["role"],
        "brand_status": brand["status"] if brand else None,
    }


@router.post("/join-with-invite", response_model=InviteJoinResponse)
async def join_with_invite(payload: JoinInviteRequest):
    try:
        result = await AuthService.join_with_invite(
            payload.email,
            payload.invite_code,
            payload.full_name,
            payload.password,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if result is None:
        raise HTTPException(status_code=400, detail="Invalid or expired invite")

    return {
        "message": "Invite accepted successfully",
        "brand": result["brand"],
        "user": _strip_password_hash(result["user"]),
    }


@router.get("/registration-status")
async def get_registration_status(email: str):
    if not email or not email.strip():
        raise HTTPException(status_code=400, detail="Email is required")

    status_info = await AuthService.get_registration_status(email.strip())
    if status_info is None:
        raise HTTPException(status_code=404, detail="No registration found for this email")

    return status_info
