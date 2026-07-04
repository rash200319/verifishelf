import asyncio
import logging

from app.core import db
from app.core.celery import celery
from app.core.marketplaces import DARAZ_COUNTRY_CODE
from app.services.crawl_scheduler_service import CrawlSchedulerService
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


async def _run_brand_crawl(crawl_job_id: int, brand_id: int, country_code: str):
    await _ensure_mysql_pool()
    try:
        return await CrawlSchedulerService.run_brand_crawl(crawl_job_id, brand_id, country_code)
    finally:
        await db.close_mysql()


async def _run_dispatch(country_code: str):
    await _ensure_mysql_pool()
    try:
        dispatch_result = await CrawlSchedulerService.dispatch_due_crawls(country_code)
        for item in dispatch_result["dispatched"]:
            try:
                run_brand_crawl.delay(item["crawl_job_id"], item["brand_id"], country_code)
            except Exception as e:
                logger.exception("Failed to enqueue run_brand_crawl for job_id=%s", item["crawl_job_id"])
                from app.repositories.crawl_job_repository import CrawlJobRepository
                from datetime import datetime
                try:
                    await CrawlJobRepository.update_job_status(item["crawl_job_id"], "failed", finished_at=datetime.now())
                except Exception:
                    logger.exception("Failed to mark job_id=%s as failed after enqueue error", item["crawl_job_id"])
        return dispatch_result
    finally:
        await db.close_mysql()


@celery.task(name="app.tasks.crawl_tasks.crawl_product")
def crawl_product(brand_id: int, product_id: int, country_code: str = "LK"):
    return asyncio.run(_run_crawl(brand_id, product_id, country_code))


@celery.task(name="app.tasks.crawl_tasks.run_brand_crawl")
def run_brand_crawl(crawl_job_id: int, brand_id: int, country_code: str = DARAZ_COUNTRY_CODE):
    return asyncio.run(_run_brand_crawl(crawl_job_id, brand_id, country_code))


@celery.task(name="app.tasks.crawl_tasks.dispatch_due_crawls")
def dispatch_due_crawls(country_code: str = DARAZ_COUNTRY_CODE):
    return asyncio.run(_run_dispatch(country_code))
