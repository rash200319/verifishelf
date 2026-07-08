from datetime import datetime

from pydantic import BaseModel, Field


class ListingInfo(BaseModel):
    id: int
    product_id: int
    seller_id: int
    marketplace_id: int
    listing_title: str
    listing_url: str
    image_url: str | None = None
    currency_code: str
    seller_name: str | None = None
    product_name: str | None = None


class ViolationResponse(BaseModel):
    id: int
    listing_id: int
    map_price: float
    advertised_price: float
    price_delta_pct: float | None = None
    classifier_confidence: float | None = None
    classifier_type: str | None = None
    status: str
    severity: str | None = None
    detected_at: datetime
    listing: ListingInfo | None = None


class EnforcementLetterResponse(BaseModel):
    id: int
    violation_id: int
    letter_content: str
    generated_by: str
    generated_at: datetime


class EnforcementGenerateRequest(BaseModel):
    provider: str = Field(default="template")
    force_regenerate: bool = False
