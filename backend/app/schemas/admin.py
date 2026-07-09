from enum import Enum

from pydantic import BaseModel, Field


class BrandPlan(str, Enum):
    starter = "starter"
    growth = "growth"
    enterprise = "enterprise"


class AdminBrandOnboardRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    plan: BrandPlan = BrandPlan.starter


class AdminUserCreateRequest(BaseModel):
    brand_id: int
    full_name: str = Field(min_length=1, max_length=255)
    email: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=255)
    role: str = Field(default="admin", max_length=50)


class BrandReviewRequest(BaseModel):
    # No reviewed_by field -- who reviewed this is derived server-side from
    # the authenticated superadmin token, never trusted from the client.
    review_notes: str | None = Field(default=None, max_length=4000)
