from datetime import date

from pydantic import BaseModel, Field, model_validator


class WeeklyReportGenerateRequest(BaseModel):
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.start_date is not None and self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class WeeklyReportSummary(BaseModel):
    listings_monitored: int
    price_snapshots: int
    violations_detected: int
    violations_open: int
    active_promo_windows: int
    repeat_offenders: int = 0


class WeeklyReportProductStat(BaseModel):
    product_id: int
    product_name: str
    map_price: float
    avg_observed_price: float | None
    snapshot_count: int
    latest_price: float | None
    price_90d_start: float | None = None
    price_90d_end: float | None = None
    price_drift_pct: float | None = None


class WeeklyReportOffendingSeller(BaseModel):
    seller_id: int
    seller_name: str
    violation_count: int
    listing_url: str | None = None


class WeeklyReportResponse(BaseModel):
    id: int
    brand_id: int
    report_start_date: date
    report_end_date: date
    summary: WeeklyReportSummary
    products: list[WeeklyReportProductStat]
    top_offending_sellers: list[WeeklyReportOffendingSeller] = []
    narrative: str
    narrative_source: str = "rule_based"
    generated_at: str
