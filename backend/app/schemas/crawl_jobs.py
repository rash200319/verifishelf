from datetime import datetime

from pydantic import BaseModel


class CrawlJobResponse(BaseModel):
    id: int
    brand_id: int
    marketplace_id: int
    status: str
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


class CrawlScheduleResponse(BaseModel):
    demo_mode: bool
    marketplace: str
    country_code: str
    scheduler_tick_seconds: int
    intervals_seconds: dict[str, int]
