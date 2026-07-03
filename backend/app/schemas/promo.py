from datetime import date

from pydantic import BaseModel, Field, model_validator


class PromoCreateRequest(BaseModel):
    product_id: int
    marketplace_id: int | None = None
    start_date: date
    end_date: date
    notes: str | None = None

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class PromoResponse(BaseModel):
    id: int
    brand_id: int
    product_id: int
    marketplace_id: int | None
    start_date: date
    end_date: date
    notes: str | None
    created_at: str
