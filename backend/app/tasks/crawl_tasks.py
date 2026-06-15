import asyncio

from app.core.celery import celery
from app.services.crawl_service import CrawlService


@celery.task(name="app.tasks.crawl_tasks.crawl_product")
def crawl_product(brand_id, product_id, country_code="LK"):
    return asyncio.run(CrawlService.crawl_product(brand_id, product_id, country_code))
