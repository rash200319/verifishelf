from enum import Enum

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

import db

app = FastAPI()

#----------------------------------
# startup event to initialize database connections
#----------------------------------

@app.on_event("startup")
async def startup():
    print("Starting backend...")

    try:
        await db.init_mysql()
    except Exception as e:
        print(" MySQL connection failed:", e)

    try:
        await db.init_redis()
    except Exception as e:
        print(" Redis connection failed:", e)


@app.get("/health")
async def health():
    mysql_ok = db.mysql_pool is not None
    redis_ok = db.redis_client is not None

    return {
        "status": "ok" if (mysql_ok and redis_ok) else "degraded",
        "mysql": mysql_ok,
        "redis": redis_ok
    }
#----------------------------------
# brand onboarding API endpoint
#----------------------------------
class BrandPlan(str, Enum):
    starter = "starter"
    growth = "growth"
    enterprise = "enterprise"

class BrandOnboardRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    plan: BrandPlan = BrandPlan.starter

@app.post("/brands/onboard")
async def onboard_brand(payload: BrandOnboardRequest):
    try:
        brand = await db.create_brand(payload.name, payload.plan.value)
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
