from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import require_auth, require_brand_admin
from app.repositories.product_repository import ProductRepository
from app.schemas.products import ProductCreateRequest, ProductResponse, ProductUpdateRequest

router = APIRouter(prefix="/products", tags=["products"])


def _format_product(product: dict) -> ProductResponse:
    return ProductResponse(
        id=product["id"],
        brand_id=product["brand_id"],
        name=product["name"],
        description=product["description"],
        map_price=float(product["map_price"]),
        created_at=str(product["created_at"]),
    )


@router.get("", response_model=list[ProductResponse])
async def list_products(current_user: dict = Depends(require_auth)):
    try:
        products = await ProductRepository.list_products_for_brand(current_user["brand_id"])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return [_format_product(product) for product in products]


@router.post("", response_model=ProductResponse)
async def create_product(payload: ProductCreateRequest, current_user: dict = Depends(require_brand_admin)):
    # Admin-only: adds a new MAP-tracked product to this brand's catalog and
    # crawl targets -- an analyst adding one unchecked would change what the
    # whole brand monitors with no second sign-off.
    try:
        product = await ProductRepository.create_product(
            current_user["brand_id"], payload.name, payload.description, payload.map_price
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return _format_product(product)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    payload: ProductUpdateRequest,
    current_user: dict = Depends(require_brand_admin),
):
    try:
        product = await ProductRepository.update_product(
            product_id, current_user["brand_id"], payload.name, payload.description, payload.map_price
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return _format_product(product)
