from fastapi import APIRouter, HTTPException

from app.core.auth import create_access_token
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    session = await AuthService.login(payload.email, payload.password, payload.brand_name)
    if session is None:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = session["user"]
    brand = session["brand"]
    token = create_access_token(
        {
            "sub": user["email"],
            "user_id": user["id"],
            "brand_id": brand["id"],
            "brand_name": brand["name"],
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
    }
