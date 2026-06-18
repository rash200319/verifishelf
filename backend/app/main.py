import asyncio
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.admin import router as admin_router
from app.api.routes.crawl import router as crawl_router
from app.api.routes.health import router as health_router
from app.api.routes.promos import router as promos_router
from app.api.routes.reports import router as reports_router
from app.core import db

app = FastAPI(title="VerifyShelf Backend")
redis_health_task = None

cors_origins = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
cors_origin_regex = os.getenv(
    "CORS_ALLOW_ORIGIN_REGEX",
    r"^https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|(?:10|192\.168|172\.(?:1[6-9]|2\d|3[0-1]))\.\d{1,3}\.\d{1,3})(?::3000)$",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in cors_origins.split(",") if origin.strip()],
    allow_origin_regex=cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
app.include_router(promos_router)
app.include_router(reports_router)
app.include_router(crawl_router)
