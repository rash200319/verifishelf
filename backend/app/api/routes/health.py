from fastapi import APIRouter

from app.core import db

router = APIRouter()


@router.get("/health")
async def health():
    mysql_ok = db.mysql_pool is not None
    redis_ok = db.redis_health_ok

    return {
        "status": "ok" if (mysql_ok and redis_ok) else "degraded",
        "mysql": mysql_ok,
        "redis": redis_ok,
    }
