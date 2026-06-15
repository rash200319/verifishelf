from datetime import datetime

from app.core.crawl_schedule import get_crawl_interval_for_plan, is_demo_mode
from app.core.marketplaces import DARAZ_COUNTRY_CODE, DARAZ_MARKETPLACE_ID
from app.repositories.crawl_job_repository import CrawlJobRepository
from app.repositories.product_repository import ProductRepository


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
    async def is_brand_due(cls, brand_id: int, plan: str, marketplace_id: int = DARAZ_MARKETPLACE_ID) -> bool:
        latest_job = await CrawlJobRepository.get_latest_job(brand_id, marketplace_id)
        if latest_job is None:
            return True

        if latest_job["status"] in {"queued", "running"}:
            return False

        interval_seconds = get_crawl_interval_for_plan(plan)
        elapsed = cls._seconds_since(latest_job.get("finished_at") or latest_job.get("created_at"))
        return elapsed >= interval_seconds

    @classmethod
    async def dispatch_due_crawls(cls, country_code: str = DARAZ_COUNTRY_CODE) -> dict:
        targets = await ProductRepository.list_brand_product_targets()
        grouped = cls._group_targets_by_brand(targets)

        dispatched = []
        skipped = []

        for brand in grouped.values():
            brand_id = brand["brand_id"]
            plan = brand["brand_plan"]

            if not await cls.is_brand_due(brand_id, plan):
                skipped.append({"brand_id": brand_id, "reason": "interval_not_elapsed"})
                continue

            job = await CrawlJobRepository.create_job(brand_id, DARAZ_MARKETPLACE_ID, status="queued")
            dispatched.append(
                {
                    "brand_id": brand_id,
                    "brand_plan": plan,
                    "crawl_job_id": job["id"],
                    "product_count": len(brand["products"]),
                    "interval_seconds": get_crawl_interval_for_plan(plan),
                }
            )

        return {
            "demo_mode": is_demo_mode(),
            "country_code": country_code,
            "dispatched": dispatched,
            "skipped": skipped,
        }

    @classmethod
    async def run_brand_crawl(
        cls,
        crawl_job_id: int,
        brand_id: int,
        country_code: str = DARAZ_COUNTRY_CODE,
    ) -> dict:
        await CrawlJobRepository.update_job_status(crawl_job_id, "running", started_at=datetime.now())

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
            result = await CrawlService.crawl_product(brand_id, int(product["id"]), country_code)
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
