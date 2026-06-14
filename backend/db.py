import os
import aiomysql
import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()

mysql_pool = None
redis_client = None


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
    global redis_client
    redis_client = redis.Redis(
        host=os.getenv("REDIS_HOST"),
        port=int(os.getenv("REDIS_PORT")),
        decode_responses=True,
    )

    await redis_client.ping()
    print(" Redis connected")