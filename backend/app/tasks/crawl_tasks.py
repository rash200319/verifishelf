import asyncio
import logging

from app.core import db
from app.core.celery import celery
from app.services.crawl_service import CrawlService

logger = logging.getLogger(__name__)


async def _ensure_mysql_pool():
    if db.mysql_pool is not None:
        await db.close_mysql()
    await db.init_mysql()


async def _run_crawl(brand_id: int, product_id: int, country_code: str):
    await _ensure_mysql_pool()
    try:
        return await CrawlService.crawl_product(brand_id, product_id, country_code)
    finally:
        await db.close_mysql()


@celery.task(name="app.tasks.crawl_tasks.crawl_product")
def crawl_product(brand_id: int, product_id: int, country_code: str = "LK"):
    return asyncio.run(_run_crawl(brand_id, product_id, country_code))
