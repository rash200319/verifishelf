import os

from celery import Celery

from app.core.marketplaces import DEMO_BRAND_ID, DEMO_PRODUCT_ID, DARAZ_COUNTRY_CODE

celery = Celery(
    "verifishelf",
    broker=f"redis://{os.getenv('REDIS_HOST', '127.0.0.1')}:{os.getenv('REDIS_PORT', '6379')}/0",
    backend=f"redis://{os.getenv('REDIS_HOST', '127.0.0.1')}:{os.getenv('REDIS_PORT', '6379')}/1",
)

celery.conf.timezone = "Asia/Colombo"
celery.conf.enable_utc = False
celery.conf.beat_schedule = {
    "daraz-crawl-every-minute": {
        "task": "app.tasks.crawl_tasks.crawl_product",
        "schedule": float(os.getenv("CRAWL_BEAT_INTERVAL_SECONDS", "60")),
        "args": (
            int(os.getenv("CRAWL_BRAND_ID", str(DEMO_BRAND_ID))),
            int(os.getenv("CRAWL_PRODUCT_ID", str(DEMO_PRODUCT_ID))),
            os.getenv("CRAWL_COUNTRY_CODE", DARAZ_COUNTRY_CODE),
        ),
    }
}

celery.autodiscover_tasks(["app"])