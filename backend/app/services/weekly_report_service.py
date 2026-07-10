import json
from datetime import date, timedelta

from app.repositories.brand_repository import BrandRepository
from app.repositories.weekly_report_repository import WeeklyReportRepository
from app.services import llm_client


class WeeklyReportService:
    # Fallback values for reports generated before report_content was a
    # structured JSON payload (or any row whose summary is otherwise
    # incomplete) -- merged under content["summary"] so a legacy/partial
    # row renders with zeros instead of failing WeeklyReportResponse's
    # required-field validation for the whole brand's report list.
    _EMPTY_SUMMARY = {
        "listings_monitored": 0,
        "price_snapshots": 0,
        "violations_detected": 0,
        "violations_open": 0,
        "active_promo_windows": 0,
    }

    NARRATIVE_SYSTEM_PROMPT = (
        "You are a brand-protection analyst writing a weekly MAP-monitoring "
        "report for a client brand. Write 2-4 short paragraphs of plain-English "
        "narrative summarizing the week's monitoring activity, referencing only "
        "the numbers and product names given -- do not invent figures, trends, "
        "or products not present in the data. Be direct and factual, not "
        "salesy. Output only the narrative text, no headers or preamble."
    )

    @staticmethod
    def _default_date_range():
        end_date = date.today()
        start_date = end_date - timedelta(days=6)
        return start_date, end_date

    @staticmethod
    def _to_float(value) -> float | None:
        if value is None:
            return None
        return float(value)

    @classmethod
    def _build_narrative_with_llm(
        cls, brand_name: str, start_date: date, end_date: date, summary: dict, products: list
    ) -> tuple[str, str] | None:
        prompt = (
            f"Brand: {brand_name}\n"
            f"Period: {start_date.isoformat()} to {end_date.isoformat()}\n"
            f"Summary: {json.dumps(summary)}\n"
            f"Product stats: {json.dumps(products)}\n"
        )
        return llm_client.generate_text(cls.NARRATIVE_SYSTEM_PROMPT, prompt, max_tokens=500)

    @staticmethod
    def _build_narrative(brand_name: str, start_date: date, end_date: date, summary: dict, products: list) -> str:
        lines = [
            f"Weekly MAP monitoring report for {brand_name}",
            f"Period: {start_date.isoformat()} to {end_date.isoformat()}",
            "",
            f"Listings monitored: {summary['listings_monitored']}",
            f"Price snapshots captured: {summary['price_snapshots']}",
            f"Violations detected: {summary['violations_detected']} ({summary['violations_open']} still open)",
            f"Active promo windows overlapping this period: {summary['active_promo_windows']}",
        ]

        if products:
            lines.append("")
            lines.append("Product highlights:")
            for product in products:
                avg_price = WeeklyReportService._to_float(product.get("avg_observed_price"))
                map_price = WeeklyReportService._to_float(product.get("map_price"))
                latest_price = WeeklyReportService._to_float(product.get("latest_price"))
                avg_text = f"{avg_price:.2f}" if avg_price is not None else "n/a"
                latest_text = f"{latest_price:.2f}" if latest_price is not None else "n/a"
                lines.append(
                    f"- {product['product_name']}: MAP {map_price:.2f}, "
                    f"avg observed {avg_text}, latest {latest_text}, "
                    f"{int(product.get('snapshot_count') or 0)} snapshots"
                )

        return "\n".join(lines)

    @staticmethod
    def _serialize_product_row(row: dict) -> dict:
        return {
            "product_id": int(row["product_id"]),
            "product_name": row["product_name"],
            "map_price": WeeklyReportService._to_float(row["map_price"]) or 0.0,
            "avg_observed_price": WeeklyReportService._to_float(row.get("avg_observed_price")),
            "snapshot_count": int(row.get("snapshot_count") or 0),
            "latest_price": WeeklyReportService._to_float(row.get("latest_price")),
        }

    @classmethod
    def _build_report_payload(cls, brand_name: str, start_date: date, end_date: date, metrics: dict) -> dict:
        summary = metrics["summary"]
        products = [cls._serialize_product_row(row) for row in metrics["products"]]

        llm_result = cls._build_narrative_with_llm(brand_name, start_date, end_date, summary, products)
        if llm_result is not None:
            narrative, narrative_source = llm_result
        else:
            narrative = cls._build_narrative(brand_name, start_date, end_date, summary, products)
            narrative_source = "rule_based"

        return {
            "summary": summary,
            "products": products,
            "narrative": narrative,
            "narrative_source": narrative_source,
        }

    @staticmethod
    def _format_report_row(row: dict) -> dict:
        content = {}
        if row.get("report_content"):
            try:
                content = json.loads(row["report_content"])
            except json.JSONDecodeError:
                content = {
                    "summary": {},
                    "products": [],
                    "narrative": row["report_content"]
                }
        return {
            "id": row["id"],
            "brand_id": row["brand_id"],
            "report_start_date": row["report_start_date"],
            "report_end_date": row["report_end_date"],
            "summary": {**WeeklyReportService._EMPTY_SUMMARY, **content.get("summary", {})},
            "products": content.get("products", []),
            "narrative": content.get("narrative", ""),
            "narrative_source": content.get("narrative_source", "rule_based"),
            "generated_at": row["generated_at"],
        }

    @classmethod
    async def generate_report(cls, brand_id: int, start_date: date | None = None, end_date: date | None = None):
        if start_date is None or end_date is None:
            default_start, default_end = cls._default_date_range()
            start_date = start_date or default_start
            end_date = end_date or default_end

        if end_date < start_date:
            raise ValueError("end_date must be on or after start_date")

        brand = await BrandRepository.get_brand_by_id(brand_id)
        if brand is None:
            raise ValueError(f"Brand {brand_id} not found")

        metrics = await WeeklyReportRepository.aggregate_brand_metrics(brand_id, start_date, end_date)
        payload = cls._build_report_payload(brand["name"], start_date, end_date, metrics)
        stored = await WeeklyReportRepository.create_report(brand_id, start_date, end_date, payload)
        return cls._format_report_row(stored)

    @classmethod
    async def list_reports(cls, brand_id: int, limit: int = 20):
        rows = await WeeklyReportRepository.list_reports(brand_id, limit)
        return [cls._format_report_row(row) for row in rows]

    @classmethod
    async def get_report(cls, brand_id: int, report_id: int):
        row = await WeeklyReportRepository.get_report(report_id, brand_id)
        if row is None:
            return None
        return cls._format_report_row(row)
