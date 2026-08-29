from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import db
from app.models import Brand, Product


class ProductRepository:
    _FIELDS = ["id", "brand_id", "name", "description", "map_price", "created_at"]

    @staticmethod
    async def get_product_for_brand(
        product_id: int,
        brand_id: int,
        session: AsyncSession | None = None,
    ):
        async with db.session_scope(session) as s:
            stmt = select(Product).where(
                Product.id == product_id,
                Product.brand_id == brand_id,
            )
            row = (await s.execute(stmt)).scalar_one_or_none()
            return db.model_to_dict(row, ProductRepository._FIELDS)

    @staticmethod
    async def list_products_for_brand(brand_id: int, session: AsyncSession | None = None):
        async with db.session_scope(session) as s:
            stmt = (
                select(Product)
                .where(Product.brand_id == brand_id)
                .order_by(Product.id)
            )
            rows = (await s.execute(stmt)).scalars().all()
            return [db.model_to_dict(row, ProductRepository._FIELDS) for row in rows]

    @staticmethod
    async def create_product(
        brand_id: int,
        name: str,
        description: str | None,
        map_price: float,
        session: AsyncSession | None = None,
    ):
        async with db.session_scope(session) as s:
            product = Product(
                brand_id=brand_id,
                name=name,
                description=description,
                map_price=map_price,
            )
            s.add(product)
            await s.flush()
            await s.refresh(product)
            return db.model_to_dict(product, ProductRepository._FIELDS)

    @staticmethod
    async def update_product(
        product_id: int,
        brand_id: int,
        name: str,
        description: str | None,
        map_price: float,
        session: AsyncSession | None = None,
    ):
        async with db.session_scope(session) as s:
            stmt = select(Product).where(
                Product.id == product_id,
                Product.brand_id == brand_id,
            )
            product = (await s.execute(stmt)).scalar_one_or_none()
            if product is None:
                return None

            product.name = name
            product.description = description
            product.map_price = map_price
            await s.flush()
            await s.refresh(product)
            return db.model_to_dict(product, ProductRepository._FIELDS)

    @staticmethod
    async def list_brand_product_targets(session: AsyncSession | None = None):
        async with db.session_scope(session) as s:
            stmt = (
                select(
                    Brand.id.label("brand_id"),
                    Brand.name.label("brand_name"),
                    Brand.plan.label("brand_plan"),
                    Product.id.label("product_id"),
                    Product.name.label("product_name"),
                )
                .join(Product, Product.brand_id == Brand.id)
                .order_by(Brand.id, Product.id)
            )
            rows = (await s.execute(stmt)).mappings().all()
            return [dict(row) for row in rows]
