import asyncio

from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.admin import router as admin_router
from app.api.routes.health import router as health_router
from app.core import db

app = FastAPI(title="VerifyShelf Backend")
redis_health_task = None


@app.on_event("startup")
async def startup():
    global redis_health_task
    print("Starting backend...")

    try:
        await db.init_mysql()
    except Exception as e:
        print(" MySQL connection failed:", e)

    try:
        await db.init_redis()
        redis_health_task = asyncio.create_task(db.monitor_redis_health())
    except Exception as e:
        print(" Redis connection failed:", e)


@app.on_event("shutdown")
async def shutdown():
    global redis_health_task

    if redis_health_task is not None:
        redis_health_task.cancel()
        try:
            await redis_health_task
        except asyncio.CancelledError:
            pass


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(admin_router)
