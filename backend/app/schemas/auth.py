from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=255)


class BrandRegisterRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=255)
    brand_name: str = Field(min_length=1, max_length=255)
    business_url: str = Field(min_length=1, max_length=2048)
    company_name: str = Field(min_length=1, max_length=255)
    notes: str | None = Field(default=None, max_length=4000)


class JoinInviteRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=255)
    invite_code: str = Field(min_length=1, max_length=255)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    brand_id: int
    brand_name: str
    role: str
    brand_status: str


class BrandRegisterResponse(BaseModel):
    message: str
    brand: dict
    user: dict


class InviteJoinResponse(BaseModel):
    message: str
    brand: dict
    user: dict
