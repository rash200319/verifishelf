from datetime import datetime

from app.core.crawl_schedule import get_crawl_interval_for_plan, is_demo_mode
from app.core.marketplaces import ACTIVE_COUNTRY_CODE
from app.repositories.crawl_job_repository import CrawlJobRepository
from app.repositories.product_repository import ProductRepository
from app.core import db
from aiomysql.cursors import DictCursor


class CrawlSchedulerService:
    @staticmethod
    def _seconds_since(timestamp) -> float:
        if timestamp is None:
            return float("inf")

        if isinstance(timestamp, datetime):
            reference = timestamp
        else:
            reference = datetime.fromisoformat(str(timestamp))

        return (datetime.now() - reference).total_seconds()

    @staticmethod
    def _group_targets_by_brand(targets: list[dict]) -> dict[int, dict]:
        grouped: dict[int, dict] = {}

        for target in targets:
            brand_id = int(target["brand_id"])
            if brand_id not in grouped:
                grouped[brand_id] = {
                    "brand_id": brand_id,
                    "brand_name": target["brand_name"],
                    "brand_plan": target["brand_plan"],
                    "products": [],
                }

            grouped[brand_id]["products"].append(
                {
                    "product_id": int(target["product_id"]),
                    "product_name": target["product_name"],
                }
            )

        return grouped

    @classmethod
    async def _load_enabled_brand_marketplaces(cls) -> list[dict]:
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT
                        bm.id AS brand_marketplace_id,
                        bm.brand_id,
                        bm.marketplace_id,
                        bm.enabled,
                        bm.crawl_frequency_hrs,
                        bm.country_code,
                        bm.priority,
                        b.name AS brand_name,
                        b.plan AS brand_plan,
                        m.name AS marketplace_name,
                        m.country_code AS marketplace_country_code
                    FROM brand_marketplaces bm
                    INNER JOIN brands b ON b.id = bm.brand_id
                    INNER JOIN marketplaces m ON m.id = bm.marketplace_id
                    WHERE bm.enabled = TRUE AND b.status = 'approved'
                    ORDER BY bm.brand_id, bm.priority ASC, bm.marketplace_id ASC
                    """
                )
                return await cur.fetchall()

    @classmethod
    async def is_brand_due(cls, brand_id: int, plan: str, marketplace_id: int) -> bool:
        latest_job = await CrawlJobRepository.get_latest_job(brand_id, marketplace_id)
        if latest_job is None:
            return True

        if latest_job["status"] in {"queued", "running"}:
            return False

        interval_seconds = get_crawl_interval_for_plan(plan)
        elapsed = cls._seconds_since(latest_job.get("finished_at") or latest_job.get("created_at"))
        return elapsed >= interval_seconds

    @classmethod
    async def dispatch_due_crawls(cls, country_code: str = ACTIVE_COUNTRY_CODE) -> dict:
        brand_marketplaces = await cls._load_enabled_brand_marketplaces()

        dispatched = []
        skipped = []

        for setting in brand_marketplaces:
            brand_id = int(setting["brand_id"])
            marketplace_id = int(setting["marketplace_id"])
            plan = setting["brand_plan"]
            marketplace_country_code = setting.get("country_code") or setting.get("marketplace_country_code") or country_code

            if not await cls.is_brand_due(brand_id, plan, marketplace_id):
                skipped.append({"brand_id": brand_id, "marketplace_id": marketplace_id, "reason": "interval_not_elapsed"})
                continue

            job = await CrawlJobRepository.create_job(brand_id, marketplace_id, status="queued")
            dispatched.append(
                {
                    "brand_id": brand_id,
                    "brand_plan": plan,
                    "brand_marketplace_id": int(setting["brand_marketplace_id"]),
                    "marketplace_id": marketplace_id,
                    "marketplace_name": setting["marketplace_name"],
                    "country_code": marketplace_country_code,
                    "crawl_job_id": job["id"],
                    "interval_seconds": int(
                        (setting["crawl_frequency_hrs"] * 3600)
                        if setting["crawl_frequency_hrs"] is not None
                        else get_crawl_interval_for_plan(plan)
                    ),
                }
            )

        return {
            "demo_mode": is_demo_mode(),
            "country_code": country_code,
            "dispatched": dispatched,
            "skipped": skipped,
        }

    @classmethod
    async def get_enabled_target_for_brand(cls, brand_id: int) -> dict | None:
        """
        The brand's own enabled, approved marketplace target (lowest
        priority number first) -- the same row dispatch_due_crawls would
        eventually pick for this brand, used by trigger_crawl_now to run
        it on demand instead of waiting for the scheduler tick.
        """
        if db.mysql_pool is None:
            raise RuntimeError("MySQL pool is not initialized")

        async with db.mysql_pool.acquire() as conn:
            async with conn.cursor(DictCursor) as cur:
                await cur.execute(
                    """
                    SELECT
                        bm.marketplace_id,
                        bm.country_code,
                        m.country_code AS marketplace_country_code
                    FROM brand_marketplaces bm
                    INNER JOIN brands b ON b.id = bm.brand_id
                    INNER JOIN marketplaces m ON m.id = bm.marketplace_id
                    WHERE bm.brand_id = %s AND bm.enabled = TRUE AND b.status = 'approved'
                    ORDER BY bm.priority ASC, bm.marketplace_id ASC
                    LIMIT 1
                    """,
                    (brand_id,),
                )
                row = await cur.fetchone()
                if row is None:
                    return None
                return {
                    "marketplace_id": int(row["marketplace_id"]),
                    "country_code": row.get("country_code") or row.get("marketplace_country_code") or ACTIVE_COUNTRY_CODE,
                }

    @classmethod
    async def trigger_crawl_now(cls, brand_id: int) -> dict:
        """
        Manually enqueue an immediate crawl for a brand, bypassing the
        plan-interval cadence check in dispatch_due_crawls -- this is the
        on-demand "run now" path (vs. the automatic scheduler tick), so a
        user can force a crawl instead of waiting for the next interval.
        Idempotent: if a job is already queued/running for this brand's
        target, that job is returned instead of enqueuing a duplicate.
        """
        target = await cls.get_enabled_target_for_brand(brand_id)
        if target is None:
            raise ValueError("This brand has no enabled, approved marketplace to crawl")

        marketplace_id = target["marketplace_id"]
        country_code = target["country_code"]

        existing = await CrawlJobRepository.get_latest_job(brand_id, marketplace_id)
        if existing is not None and existing["status"] in {"queued", "running"}:
            return {"job": existing, "country_code": country_code, "already_running": True}

        job = await CrawlJobRepository.create_job(brand_id, marketplace_id, status="queued")
        return {"job": job, "country_code": country_code, "already_running": False}

    @classmethod
    async def run_brand_crawl(
        cls,
        crawl_job_id: int,
        brand_id: int,
        country_code: str = ACTIVE_COUNTRY_CODE,
    ) -> dict:
        await CrawlJobRepository.update_job_status(crawl_job_id, "running", started_at=datetime.now())

        try:
            products = await ProductRepository.list_products_for_brand(brand_id)
            if not products:
                await CrawlJobRepository.update_job_status(crawl_job_id, "failed", finished_at=datetime.now())
                return {
                    "status": "failed",
                    "crawl_job_id": crawl_job_id,
                    "brand_id": brand_id,
                    "error": f"No products found for brand {brand_id}",
                    "results": [],
                }

            from app.services.crawl_service import CrawlService

            results = []
            failed = False

            for product in products:
                result = await CrawlService.crawl_product(brand_id, int(product["id"]), country_code, crawl_job_id=crawl_job_id)
                results.append(result)
                if result.get("status") != "ok":
                    failed = True

            final_status = "failed" if failed else "completed"
            await CrawlJobRepository.update_job_status(crawl_job_id, final_status, finished_at=datetime.now())

            return {
                "status": final_status,
                "crawl_job_id": crawl_job_id,
                "brand_id": brand_id,
                "country_code": country_code,
                "results": results,
            }
        except Exception as exc:
            import logging
            logging.getLogger(__name__).exception("Unhandled exception during brand crawl %s for brand %s", crawl_job_id, brand_id)
            try:
                await CrawlJobRepository.update_job_status(crawl_job_id, "failed", finished_at=datetime.now())
            except Exception:
                logging.getLogger(__name__).exception("Failed to update status for job %s to failed", crawl_job_id)
            return {
                "status": "failed",
                "crawl_job_id": crawl_job_id,
                "brand_id": brand_id,
                "error": str(exc),
                "results": [],
            }
