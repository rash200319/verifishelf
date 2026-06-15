from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth import require_auth
from app.schemas.promo import PromoCreateRequest, PromoResponse
from app.services.promo_service import PromoService

router = APIRouter(prefix="/promos", tags=["promos"])


def _format_promo(promo: dict) -> PromoResponse:
    return PromoResponse(
        id=promo["id"],
        brand_id=promo["brand_id"],
        product_id=promo["product_id"],
        marketplace_id=promo["marketplace_id"],
        start_date=promo["start_date"],
        end_date=promo["end_date"],
        notes=promo["notes"],
        created_at=str(promo["created_at"]),
    )


@router.post("", response_model=PromoResponse)
async def create_promo(payload: PromoCreateRequest, current_user: dict = Depends(require_auth)):
    try:
        promo = await PromoService.create_promo(
            current_user["brand_id"],
            payload.product_id,
            payload.marketplace_id,
            payload.start_date,
            payload.end_date,
            payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return _format_promo(promo)


@router.get("", response_model=list[PromoResponse])
async def list_promos(
    product_id: int | None = Query(default=None),
    active_on: date | None = Query(default=None),
    current_user: dict = Depends(require_auth),
):
    try:
        promos = await PromoService.list_promos(current_user["brand_id"], product_id, active_on)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return [_format_promo(promo) for promo in promos]
