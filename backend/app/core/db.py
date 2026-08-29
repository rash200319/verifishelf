from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional
from urllib.parse import quote_plus

import redis.asyncio as redis
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

load_dotenv()

engine: AsyncEngine | None = None
SessionLocal: async_sessionmaker[AsyncSession] | None = None
# Back-compat alias used by health checks / older references during migration.
mysql_pool = None

redis_client = None
redis_health_ok = False


def _database_url() -> str:
    user = quote_plus(os.getenv("MYSQL_USER", ""))
    password = quote_plus(os.getenv("MYSQL_PASSWORD", ""))
    host = os.getenv("MYSQL_HOST", "127.0.0.1")
    port = os.getenv("MYSQL_PORT", "3306")
    database = os.getenv("MYSQL_DB", "verifishelf")
    return f"mysql+aiomysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"


async def init_mysql():
    global engine, SessionLocal, mysql_pool

    if engine is not None:
        await close_mysql()

    engine = create_async_engine(
        _database_url(),
        pool_pre_ping=True,
        pool_recycle=3600,
    )
    SessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    # Non-None sentinel so existing `is not None` checks still work.
    mysql_pool = engine
    print(" MySQL connected")


async def close_mysql():
    global engine, SessionLocal, mysql_pool

    if engine is not None:
        await engine.dispose()
    engine = None
    SessionLocal = None
    mysql_pool = None


def require_session_factory() -> async_sessionmaker[AsyncSession]:
    if SessionLocal is None:
        raise RuntimeError("MySQL is not initialized")
    return SessionLocal


@asynccontextmanager
async def session_scope(
    session: Optional[AsyncSession] = None,
) -> AsyncIterator[AsyncSession]:
    """Yield an AsyncSession.

    If ``session`` is provided, the caller owns commit/rollback.
    Otherwise open a short-lived session and commit on success.
    """
    if session is not None:
        yield session
        return

    factory = require_session_factory()
    async with factory() as owned:
        try:
            yield owned
            await owned.commit()
        except Exception:
            await owned.rollback()
            raise


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields a request-scoped session."""
    factory = require_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def model_to_dict(obj: Any, fields: list[str] | None = None) -> dict[str, Any] | None:
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj
    cols = fields or [c.key for c in obj.__table__.columns]
    return {name: getattr(obj, name) for name in cols}


async def ping_mysql() -> bool:
    if engine is None:
        return False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


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
