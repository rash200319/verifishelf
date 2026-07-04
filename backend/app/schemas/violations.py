from datetime import datetime
from pydantic import BaseModel

class ListingInfo(BaseModel):
    id: int
    product_id: int
    seller_id: int
    marketplace_id: int
    listing_title: str
    listing_url: str
    image_url: str | None = None
    currency_code: str

class ViolationResponse(BaseModel):
    id: int
    listing_id: int
    map_price: float
    advertised_price: float
    price_delta_pct: float | None = None
    classifier_confidence: float | None = None
    classifier_type: str | None = None
    status: str
    detected_at: datetime
    listing: ListingInfo | None = None
