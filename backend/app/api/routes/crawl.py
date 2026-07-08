from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import require_auth
from app.core.crawl_schedule import (
    CRAWL_SCHEDULER_TICK_SECONDS,
    DEMO_PLAN_CRAWL_INTERVALS,
    PLAN_CRAWL_INTERVALS,
    is_demo_mode,
)
from app.core.marketplaces import (
    ACTIVE_COUNTRY_CODE,
    ACTIVE_MARKETPLACE_NAME,
    ALL_MARKETPLACES,
)
from app.repositories.crawl_job_repository import CrawlJobRepository
from app.schemas.crawl_jobs import CrawlJobResponse, CrawlScheduleResponse
from app.schemas.marketplace_config import MarketplaceConfigRecord
from app.schemas.marketplace_preview import MarketplacePreviewRecord
from app.services.marketplace_preview_service import load_marketplace_previews

router = APIRouter(prefix="/crawl", tags=["crawl"])


def _format_job(job: dict) -> CrawlJobResponse:
    return CrawlJobResponse(
        id=job["id"],
        brand_id=job["brand_id"],
        marketplace_id=job["marketplace_id"],
        status=job["status"],
        started_at=job["started_at"],
        finished_at=job["finished_at"],
        created_at=job["created_at"],
    )


@router.get("/marketplaces", response_model=list[MarketplaceConfigRecord])
async def list_marketplaces(current_user: dict = Depends(require_auth)):
    """Return all registered marketplaces and their scraping status.

    ``is_active=True`` marks the marketplace whose crawl pipeline is
    currently live.  ``scraping_status`` is either ``'live'`` or
    ``'phase_two'``.
    """
    return [MarketplaceConfigRecord(**m) for m in ALL_MARKETPLACES]


@router.get("/schedule", response_model=CrawlScheduleResponse)
async def get_crawl_schedule(current_user: dict = Depends(require_auth)):
    intervals = DEMO_PLAN_CRAWL_INTERVALS if is_demo_mode() else PLAN_CRAWL_INTERVALS
    return CrawlScheduleResponse(
        demo_mode=is_demo_mode(),
        marketplace=ACTIVE_MARKETPLACE_NAME,
        country_code=ACTIVE_COUNTRY_CODE,
        scheduler_tick_seconds=CRAWL_SCHEDULER_TICK_SECONDS,
        intervals_seconds=intervals,
    )


@router.get("/marketplace-preview", response_model=list[MarketplacePreviewRecord])
async def get_marketplace_preview(current_user: dict = Depends(require_auth)):
    try:
        return load_marketplace_previews()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/jobs", response_model=list[CrawlJobResponse])
async def list_crawl_jobs(current_user: dict = Depends(require_auth)):
    try:
        jobs = await CrawlJobRepository.list_jobs_for_brand(current_user["brand_id"])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return [_format_job(job) for job in jobs]


@router.get("/jobs/{job_id}", response_model=CrawlJobResponse)
async def get_crawl_job(job_id: int, current_user: dict = Depends(require_auth)):
    try:
        job = await CrawlJobRepository.get_job(job_id, current_user["brand_id"])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if job is None:
        raise HTTPException(status_code=404, detail="Crawl job not found")

    return _format_job(job)
