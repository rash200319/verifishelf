from fastapi import APIRouter

from app.core import db

router = APIRouter()


@router.get("/health")
async def health():
    mysql_ok = await db.ping_mysql()
    redis_ok = db.redis_health_ok

    return {
        "status": "ok" if (mysql_ok and redis_ok) else "degraded",
        "mysql": mysql_ok,
        "redis": redis_ok,
    }
