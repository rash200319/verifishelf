from pydantic import BaseModel, HttpUrl
from typing import List


class ScrapedProduct(BaseModel):
    marketplace: str = "Daraz"
    product_id: int        # Map from pdt_sku
    variant_id: int        # Map from pdt_simplesku
    title: str             # Map from pdt_name
    price_raw: str         # Map from pdt_price ("Rs. 21,058")
    currency: str          # Map from currencyCode ("LKR")
    brand: str             # Map from brand_name
    category_path: List[str] # Map from pdt_category
    main_image: HttpUrl    # Map from pdt_photo
    description: str       # Map from og:description or meta description
    country_code: str      # Map from country
