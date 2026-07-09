from pydantic import BaseModel, Field, field_validator


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

    # Brand application / KYB fields -- collected so a superadmin has more
    # than a name and a URL to judge whether this is a real, authorized
    # brand before approving them (this product drafts enforcement letters
    # in the brand's name, so that matters more than for a typical SaaS).
    registration_number: str = Field(min_length=1, max_length=255)
    business_address: str = Field(min_length=1, max_length=2000)
    industry: str = Field(min_length=1, max_length=100)
    contact_title: str = Field(min_length=1, max_length=150)
    contact_phone: str = Field(min_length=1, max_length=50)
    estimated_sku_range: str = Field(min_length=1, max_length=50)
    current_marketplaces: list[str] = Field(min_length=1)
    authorized_attestation: bool

    @field_validator("authorized_attestation")
    @classmethod
    def must_attest(cls, value: bool) -> bool:
        if not value:
            raise ValueError("You must confirm you are authorized to submit MAP enforcement actions on behalf of this brand")
        return value


class JoinInviteRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=255)
    invite_code: str = Field(min_length=1, max_length=255)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    # Null for a superadmin -- they aren't scoped to any brand.
    brand_id: int | None
    brand_name: str | None
    role: str
    brand_status: str | None


class PublicUser(BaseModel):
    """
    User fields safe to return in an API response. Declaring this
    explicitly (instead of typing responses as a raw `dict`) means
    FastAPI's response_model filtering strips anything not listed here --
    e.g. password_hash -- even if a future change accidentally passes it
    through, rather than relying on every call site remembering to strip it.
    """

    id: int
    brand_id: int | None
    full_name: str | None
    email: str
    role: str
    is_active: bool
    is_brand_owner: bool


class BrandRegisterResponse(BaseModel):
    message: str
    brand: dict
    user: PublicUser


class InviteJoinResponse(BaseModel):
    message: str
    brand: dict
    user: PublicUser
