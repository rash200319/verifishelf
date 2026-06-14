from fastapi import APIRouter, HTTPException

from app.schemas.brands import BrandOnboardRequest
from app.services.brand_service import BrandService

router = APIRouter(prefix="/brands", tags=["brands"])


@router.post("/onboard")
async def onboard_brand(payload: BrandOnboardRequest):
    try:
        brand = await BrandService.create_brand(payload.name, payload.plan.value)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return {
        "message": "Brand onboarded successfully",
        "brand": {
            "id": brand["id"],
            "name": brand["name"],
            "plan": brand["plan"],
            "torch_sub_id": brand["torch_sub_id"],
            "created_at": brand["created_at"],
        },
    }
