from __future__ import annotations

import json
from datetime import date, timedelta
from html import escape

from app.core.claude import ClaudeService
from app.core.pdf import html_to_pdf_bytes
from app.repositories.brand_repository import BrandRepository
from app.repositories.weekly_report_repository import WeeklyReportRepository


class WeeklyReportService:
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

    @staticmethod
    def _build_report_payload(brand_name: str, start_date: date, end_date: date, metrics: dict) -> dict:
        summary = metrics["summary"]
        products = [WeeklyReportService._serialize_product_row(row) for row in metrics["products"]]
        narrative = WeeklyReportService._build_narrative(brand_name, start_date, end_date, summary, products)

        return {
            "summary": summary,
            "products": products,
            "narrative": narrative,
        }

    @staticmethod
    def _build_report_pdf_html(brand_name: str, report: dict) -> str:
        summary = report["summary"]
        products = report["products"]
        narrative = report["narrative"]

        product_rows = []
        for product in products:
            avg_observed = product.get("avg_observed_price")
            latest_price = product.get("latest_price")
            avg_text = "n/a" if avg_observed is None else f"{float(avg_observed):.2f}"
            latest_text = "n/a" if latest_price is None else f"{float(latest_price):.2f}"
            product_rows.append(
                "<tr>"
                f"<td>{escape(product['product_name'])}</td>"
                f"<td>{float(product['map_price']):.2f}</td>"
                f"<td>{avg_text}</td>"
                f"<td>{latest_text}</td>"
                f"<td>{int(product.get('snapshot_count') or 0)}</td>"
                "</tr>"
            )

        narrative_paragraphs = []
        for paragraph in narrative.split("\n\n"):
            paragraph = paragraph.strip()
            if paragraph:
                narrative_paragraphs.append(f"<p>{escape(paragraph)}</p>")

        return f"""
        <html>
          <head>
            <meta charset="utf-8" />
            <style>
              body {{ font-family: Arial, Helvetica, sans-serif; color: #111827; padding: 36px; line-height: 1.55; }}
              .sheet {{ border: 1px solid #d1d5db; border-radius: 12px; padding: 28px; }}
              .eyebrow {{ text-transform: uppercase; letter-spacing: 0.14em; font-size: 10px; color: #6b7280; }}
              .title {{ font-size: 24px; margin: 8px 0 18px; }}
              .section-title {{ margin: 24px 0 10px; font-size: 16px; }}
              .summary {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px 18px; font-size: 13px; }}
              .summary div {{ background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 10px; padding: 10px 12px; }}
              table {{ width: 100%; border-collapse: collapse; font-size: 12px; }}
              th, td {{ border: 1px solid #e5e7eb; padding: 8px; text-align: left; vertical-align: top; }}
              th {{ background: #f3f4f6; }}
              .narrative p {{ margin: 0 0 10px; }}
            </style>
          </head>
          <body>
            <div class="sheet">
              <div class="eyebrow">Weekly MAP Monitoring Report</div>
              <div class="title">{escape(brand_name)}</div>
              <div class="summary">
                <div><strong>Listings monitored:</strong> {summary['listings_monitored']}</div>
                <div><strong>Price snapshots:</strong> {summary['price_snapshots']}</div>
                <div><strong>Violations detected:</strong> {summary['violations_detected']}</div>
                <div><strong>Violations open:</strong> {summary['violations_open']}</div>
                <div><strong>Active promo windows:</strong> {summary['active_promo_windows']}</div>
              </div>

              <div class="section-title">Product highlights</div>
              <table>
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>MAP</th>
                    <th>Avg observed</th>
                    <th>Latest</th>
                    <th>Snapshots</th>
                  </tr>
                </thead>
                <tbody>
                  {''.join(product_rows) or '<tr><td colspan="5">No products tracked in this period.</td></tr>'}
                </tbody>
              </table>

              <div class="section-title">Analyst narrative</div>
              <div class="narrative">{''.join(narrative_paragraphs)}</div>
            </div>
          </body>
        </html>
        """.strip()

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
                    "narrative": row["report_content"],
                }
        
        # If content parsed is not a dictionary (e.g. parsed a primitive or list), normalize it
        if not isinstance(content, dict):
            content = {
                "summary": {},
                "products": [],
                "narrative": str(content),
            }

        summary = content.get("summary")
        if not isinstance(summary, dict):
            summary = {}

        # Ensure all required summary fields are present as integers
        for field in [
            "listings_monitored",
            "price_snapshots",
            "violations_detected",
            "violations_open",
            "active_promo_windows",
        ]:
            if field not in summary or summary[field] is None:
                summary[field] = 0
            else:
                try:
                    summary[field] = int(summary[field])
                except (ValueError, TypeError):
                    summary[field] = 0

        return {
            "id": row["id"],
            "brand_id": row["brand_id"],
            "report_start_date": row["report_start_date"],
            "report_end_date": row["report_end_date"],
            "summary": summary,
            "products": content.get("products") if isinstance(content.get("products"), list) else [],
            "narrative": str(content.get("narrative") or ""),
            "generated_at": row["generated_at"],
        }

    @classmethod
    async def _draft_claude_narrative(
        cls,
        brand_name: str,
        start_date: date,
        end_date: date,
        summary: dict,
        products: list,
    ) -> str:
        payload = {
            "brand_name": brand_name,
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            "summary": summary,
            "products": products,
        }
        return await ClaudeService.draft_weekly_report_narrative(payload)

    @classmethod
    async def render_pdf_for_report(cls, brand_id: int, report_id: int) -> bytes | None:
        brand = await BrandRepository.get_brand_by_id(brand_id)
        if brand is None:
            return None

        report = await WeeklyReportRepository.get_report(report_id, brand_id)
        if report is None:
            return None

        formatted_report = cls._format_report_row(report)
        html = cls._build_report_pdf_html(brand["name"], formatted_report)
        return html_to_pdf_bytes(html)

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
        try:
            payload["narrative"] = await cls._draft_claude_narrative(
                brand["name"],
                start_date,
                end_date,
                payload["summary"],
                payload["products"],
            )
            payload["narrative_source"] = "claude"
        except Exception:
            payload["narrative_source"] = "template"

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
