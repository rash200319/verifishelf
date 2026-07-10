import asyncio
import logging

from app.core import db
from app.core.celery import celery
from app.repositories.brand_repository import BrandRepository
from app.services.weekly_report_service import WeeklyReportService

logger = logging.getLogger(__name__)


async def _ensure_mysql_pool():
    if db.mysql_pool is not None:
        await db.close_mysql()
    await db.init_mysql()


async def _run_generate_all_weekly_reports():
    await _ensure_mysql_pool()
    try:
        brands = await BrandRepository.list_approved_brands()
        generated = []
        for brand in brands:
            try:
                report = await WeeklyReportService.generate_report(brand["id"])
                generated.append({"brand_id": brand["id"], "report_id": report["id"]})
            except Exception:
                logger.exception("Failed to auto-generate weekly report for brand_id=%s", brand["id"])
        return {"generated": generated}
    finally:
        await db.close_mysql()


@celery.task(name="app.tasks.report_tasks.generate_all_weekly_reports")
def generate_all_weekly_reports():
    """
    Every Monday morning, auto-generate a weekly report for every approved
    brand -- previously this only ever happened when a user manually clicked
    "Generate Report" via the API. A per-brand failure (e.g. one brand's
    metrics query errors) is logged and skipped, not allowed to abort the
    whole batch.
    """
    return asyncio.run(_run_generate_all_weekly_reports())
