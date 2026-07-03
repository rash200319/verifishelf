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


class WeeklyReportProductStat(BaseModel):
    product_id: int
    product_name: str
    map_price: float
    avg_observed_price: float | None
    snapshot_count: int
    latest_price: float | None


class WeeklyReportResponse(BaseModel):
    id: int
    brand_id: int
    report_start_date: date
    report_end_date: date
    summary: WeeklyReportSummary
    products: list[WeeklyReportProductStat]
    narrative: str
    generated_at: str
