from pydantic import BaseModel, Field


class MarketplaceFeaturedItem(BaseModel):
    title: str
    url: str | None = None
    image_url: str | None = None
    rating_value: float | None = None
    rating_count: int | None = None


class MarketplacePreviewRecord(BaseModel):
    marketplace: str
    source_file: str
    source_url: str | None = None
    page_title: str | None = None
    meta_description: str | None = None
    has_next_page: bool = False
    has_json_ld: bool = False
    json_ld_types: list[str] = Field(default_factory=list)
    verification_hint: str | None = None
    featured_items: list[MarketplaceFeaturedItem] = Field(default_factory=list)
