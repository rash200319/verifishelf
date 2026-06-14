from fastapi import FastAPI
from db import init_mysql, init_redis, mysql_pool, redis_client

app = FastAPI()


@app.on_event("startup")
async def startup():
    print("Starting backend...")

    try:
        await init_mysql()
    except Exception as e:
        print(" MySQL connection failed:", e)

    try:
        await init_redis()
    except Exception as e:
        print(" Redis connection failed:", e)


@app.get("/health")
async def health():
    mysql_ok = mysql_pool is not None
    redis_ok = redis_client is not None

    return {
        "status": "ok" if (mysql_ok and redis_ok) else "degraded",
        "mysql": mysql_ok,
        "redis": redis_ok
    }