from fastapi import APIRouter, HTTPException

from app.core.auth import authenticate_user, create_access_token
from app.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    if not authenticate_user(payload.email, payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"access_token": create_access_token(payload.email), "token_type": "bearer"}
