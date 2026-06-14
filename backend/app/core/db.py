import asyncio
import os

import aiomysql
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

mysql_pool = None
redis_client = None
redis_health_ok = False


async def init_mysql():
    global mysql_pool
    mysql_pool = await aiomysql.create_pool(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT")),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        db=os.getenv("MYSQL_DB"),
        autocommit=True,
    )
    print(" MySQL connected")


async def init_redis():
    global redis_client, redis_health_ok
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST"),
        port=int(os.getenv("REDIS_PORT")),
        decode_responses=True,
    )

    await redis_client.ping()
    redis_health_ok = True
    print(" Redis connected")


async def monitor_redis_health(ping_interval_seconds: int = 30):
    global redis_health_ok

    while True:
        try:
            if redis_client is None:
                redis_health_ok = False
            else:
                await redis_client.ping()
                redis_health_ok = True
        except Exception:
            redis_health_ok = False

        await asyncio.sleep(ping_interval_seconds)
