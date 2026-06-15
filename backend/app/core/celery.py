from celery import Celery
import os

celery = Celery(
    "verifishelf",
    broker=f"redis://{os.getenv('REDIS_HOST', '127.0.0.1')}:{os.getenv('REDIS_PORT', '6379')}/0",
    backend=f"redis://{os.getenv('REDIS_HOST', '127.0.0.1')}:{os.getenv('REDIS_PORT', '6379')}/1",
)

celery.conf.timezone = "Asia/Colombo"
celery.conf.enable_utc = False
celery.conf.beat_schedule = {
    "crawl-product-every-minute": {
        "task": "app.tasks.crawl_tasks.crawl_product",
        "schedule": 60.0,
        "args": ("demo-brand", "demo-product"),
    }
}

celery.autodiscover_tasks(["app"])