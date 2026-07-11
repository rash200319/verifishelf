from pydantic import BaseModel, Field


class ProductCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    map_price: float = Field(gt=0)


class ProductUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    map_price: float = Field(gt=0)


class ProductResponse(BaseModel):
    id: int
    brand_id: int
    name: str
    description: str | None
    map_price: float
    created_at: str
