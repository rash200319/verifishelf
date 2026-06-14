from enum import Enum

from pydantic import BaseModel, Field


class BrandPlan(str, Enum):
    starter = "starter"
    growth = "growth"
    enterprise = "enterprise"


class BrandOnboardRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    plan: BrandPlan = BrandPlan.starter
