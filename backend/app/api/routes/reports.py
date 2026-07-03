from fastapi import APIRouter, Body, Depends, HTTPException

from app.core.auth import require_auth
from app.schemas.reports import WeeklyReportGenerateRequest, WeeklyReportResponse
from app.services.weekly_report_service import WeeklyReportService

router = APIRouter(prefix="/reports", tags=["reports"])


def _format_report(report: dict) -> WeeklyReportResponse:
    return WeeklyReportResponse(
        id=report["id"],
        brand_id=report["brand_id"],
        report_start_date=report["report_start_date"],
        report_end_date=report["report_end_date"],
        summary=report["summary"],
        products=report["products"],
        narrative=report["narrative"],
        generated_at=str(report["generated_at"]),
    )


@router.post("/weekly", response_model=WeeklyReportResponse)
async def generate_weekly_report(
    current_user: dict = Depends(require_auth),
    payload: WeeklyReportGenerateRequest = Body(default_factory=WeeklyReportGenerateRequest),
):
    try:
        report = await WeeklyReportService.generate_report(
            current_user["brand_id"],
            payload.start_date,
            payload.end_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return _format_report(report)


@router.get("/weekly", response_model=list[WeeklyReportResponse])
async def list_weekly_reports(current_user: dict = Depends(require_auth)):
    try:
        reports = await WeeklyReportService.list_reports(current_user["brand_id"])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return [_format_report(report) for report in reports]


@router.get("/weekly/{report_id}", response_model=WeeklyReportResponse)
async def get_weekly_report(report_id: int, current_user: dict = Depends(require_auth)):
    try:
        report = await WeeklyReportService.get_report(current_user["brand_id"], report_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    return _format_report(report)
