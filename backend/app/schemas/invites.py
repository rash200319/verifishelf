from pydantic import BaseModel, Field


class BrandInviteCreateRequest(BaseModel):
    email: str | None = Field(default=None, max_length=255)
    role: str = Field(default="analyst", max_length=50)
    expires_in_minutes: int = Field(default=60, ge=1, le=10080)


class BrandInviteResponse(BaseModel):
    message: str
    invite: dict


class BrandInviteListResponse(BaseModel):
    invites: list[dict]
