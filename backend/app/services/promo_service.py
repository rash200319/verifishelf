from datetime import date

from app.repositories.product_repository import ProductRepository
from app.repositories.promo_repository import PromoRepository


class PromoService:
    @staticmethod
    async def create_promo(
        brand_id: int,
        product_id: int,
        marketplace_id: int | None,
        start_date: date,
        end_date: date,
        notes: str | None,
    ):
        product = await ProductRepository.get_product_for_brand(product_id, brand_id)
        if product is None:
            raise ValueError(f"Product {product_id} not found for brand {brand_id}")

        return await PromoRepository.create_promo(
            brand_id,
            product_id,
            marketplace_id,
            start_date,
            end_date,
            notes,
        )

    @staticmethod
    async def list_promos(
        brand_id: int,
        product_id: int | None = None,
        active_on: date | None = None,
    ):
        return await PromoRepository.list_promos(brand_id, product_id, active_on)

    @staticmethod
    async def is_below_map_allowed(
        brand_id: int,
        product_id: int,
        marketplace_id: int | None,
        check_date: date | None = None,
    ) -> bool:
        resolved_date = check_date or date.today()
        return await PromoRepository.has_active_promo(
            brand_id,
            product_id,
            marketplace_id,
            resolved_date,
        )
