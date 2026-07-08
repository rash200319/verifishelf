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
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    brand = result["brand"]
    user = result["user"]
    return {
        "message": "Brand registration submitted for review",
        "brand": brand,
        "user": user,
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
    brand = session["brand"]
    token = create_access_token(
        {
            "sub": user["email"],
            "user_id": user["id"],
            "brand_id": brand["id"],
            "brand_name": brand["name"],
            "brand_status": brand["status"],
            "role": user["role"],
            "email": user["email"],
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user["id"],
        "brand_id": brand["id"],
        "brand_name": brand["name"],
        "role": user["role"],
        "brand_status": brand["status"],
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
        "user": result["user"],
    }


@router.get("/registration-status")
async def get_registration_status(email: str):
    if not email or not email.strip():
        raise HTTPException(status_code=400, detail="Email is required")

    status_info = await AuthService.get_registration_status(email.strip())
    if status_info is None:
        raise HTTPException(status_code=404, detail="No registration found for this email")

    return status_info
