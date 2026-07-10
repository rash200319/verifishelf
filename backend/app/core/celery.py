import os

from celery import Celery
from celery.schedules import crontab

from app.core.crawl_schedule import CRAWL_SCHEDULER_TICK_SECONDS
from app.core.marketplaces import DARAZ_COUNTRY_CODE

celery = Celery(
    "verifishelf",
    broker=f"redis://{os.getenv('REDIS_HOST', '127.0.0.1')}:{os.getenv('REDIS_PORT', '6379')}/0",
    backend=f"redis://{os.getenv('REDIS_HOST', '127.0.0.1')}:{os.getenv('REDIS_PORT', '6379')}/1",
)

celery.conf.timezone = "Asia/Colombo"
celery.conf.enable_utc = False
celery.conf.beat_schedule = {
    "dispatch-due-crawls": {
        "task": "app.tasks.crawl_tasks.dispatch_due_crawls",
        "schedule": float(CRAWL_SCHEDULER_TICK_SECONDS),
        "kwargs": {"country_code": os.getenv("CRAWL_COUNTRY_CODE", DARAZ_COUNTRY_CODE)},
    },
    "generate-weekly-reports": {
        "task": "app.tasks.report_tasks.generate_all_weekly_reports",
        # Every Monday, 06:00 Asia/Colombo -- matches celery.conf.timezone
        # above, so this doesn't silently drift to a different local time.
        "schedule": crontab(day_of_week=1, hour=6, minute=0),
    },
}

celery.autodiscover_tasks(["app"])
