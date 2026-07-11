"""
Renders a weekly report dict (see WeeklyReportService) to a PDF using
reportlab (workstream C). Pure-Python, no system dependencies -- deliberately
not weasyprint/Puppeteer, which need a system GTK/Chromium install that isn't
guaranteed to be present on every teammate's machine.
"""
from __future__ import annotations

import base64
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def render_weekly_report_pdf(brand_name: str, report: dict) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("VSTitle", parent=styles["Title"], fontSize=20, spaceAfter=4)
    subtitle_style = ParagraphStyle("VSSubtitle", parent=styles["Normal"], textColor=colors.HexColor("#475569"))
    section_style = ParagraphStyle("VSSection", parent=styles["Heading2"], spaceBefore=16, spaceAfter=8)
    body_style = ParagraphStyle("VSBody", parent=styles["Normal"], leading=16)

    story = [
        Paragraph("VerifyShelf Weekly Brand Health Report", title_style),
        Paragraph(
            f"{brand_name} &mdash; {report['report_start_date']} to {report['report_end_date']}",
            subtitle_style,
        ),
        Spacer(1, 0.2 * inch),
    ]

    summary = report.get("summary") or {}
    summary_rows = [
        ["Listings monitored", str(summary.get("listings_monitored", 0))],
        ["Price snapshots captured", str(summary.get("price_snapshots", 0))],
        ["Violations detected", str(summary.get("violations_detected", 0))],
        ["Violations still open", str(summary.get("violations_open", 0))],
        ["Active promo windows", str(summary.get("active_promo_windows", 0))],
        ["Repeat offenders", str(summary.get("repeat_offenders", 0))],
    ]
    summary_table = Table(summary_rows, colWidths=[3 * inch, 2 * inch])
    summary_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
                ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(Paragraph("Summary", section_style))
    story.append(summary_table)

    products = report.get("products") or []
    if products:
        product_rows = [["Product", "MAP Price", "Avg Observed", "Latest", "Snapshots", "90d Drift"]]
        for product in products:
            drift_pct = product.get("price_drift_pct")
            product_rows.append(
                [
                    product.get("product_name", ""),
                    f"{product.get('map_price', 0):.2f}",
                    f"{product['avg_observed_price']:.2f}" if product.get("avg_observed_price") is not None else "n/a",
                    f"{product['latest_price']:.2f}" if product.get("latest_price") is not None else "n/a",
                    str(product.get("snapshot_count", 0)),
                    f"{drift_pct:+.1f}%" if drift_pct is not None else "n/a",
                ]
            )
        product_table = Table(product_rows, colWidths=[1.9 * inch, 0.9 * inch, 1 * inch, 0.9 * inch, 0.8 * inch, 0.8 * inch])
        product_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(Paragraph("Product Highlights", section_style))
        story.append(product_table)

    top_offending_sellers = report.get("top_offending_sellers") or []
    if top_offending_sellers:
        seller_rows = [["Seller", "Violations", "Listing"]]
        for seller in top_offending_sellers:
            seller_rows.append(
                [
                    seller.get("seller_name", ""),
                    str(seller.get("violation_count", 0)),
                    seller.get("listing_url") or "n/a",
                ]
            )
        seller_table = Table(seller_rows, colWidths=[1.8 * inch, 1 * inch, 3.2 * inch])
        seller_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story.append(Paragraph("Top Offending Sellers", section_style))
        story.append(seller_table)

    narrative = (report.get("narrative") or "").strip()
    if narrative:
        story.append(Paragraph("Analyst Narrative", section_style))
        for paragraph in narrative.split("\n"):
            if paragraph.strip():
                story.append(Paragraph(paragraph.strip(), body_style))
                story.append(Spacer(1, 0.1 * inch))

    doc.build(story)
    return buffer.getvalue()


def render_enforcement_letter_pdf(context: dict, letter: dict) -> bytes:
    """Renders a generated enforcement letter (+ optional listing screenshot)
    to a PDF the brand admin can download and actually send to a reseller --
    there's no automated delivery channel (see EnforcementService.mark_sent),
    so this is the tangible artifact that action depends on."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=LETTER,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("ELTitle", parent=styles["Title"], fontSize=18, spaceAfter=4)
    subtitle_style = ParagraphStyle("ELSubtitle", parent=styles["Normal"], textColor=colors.HexColor("#475569"))
    section_style = ParagraphStyle("ELSection", parent=styles["Heading2"], spaceBefore=16, spaceAfter=8)
    body_style = ParagraphStyle("ELBody", parent=styles["Normal"], leading=16)

    story = [
        Paragraph("Enforcement Notice", title_style),
        Paragraph(
            f"{context['brand_name']} &mdash; Violation #{context['violation_id']}",
            subtitle_style,
        ),
        Spacer(1, 0.2 * inch),
    ]

    meta_rows = [
        ["Seller", context.get("seller_name") or "n/a"],
        ["Product", context.get("product_name") or "n/a"],
        ["Listing", context.get("listing_url") or "n/a"],
        ["Detected at", str(context.get("detected_at") or "n/a")],
        ["Drafted by", letter.get("generated_by", "template")],
        ["Status", letter.get("status", "draft")],
    ]
    meta_table = Table(meta_rows, colWidths=[1.3 * inch, 4.7 * inch])
    meta_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
                ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(meta_table)

    story.append(Paragraph("Letter", section_style))
    for paragraph in (letter.get("letter_content") or "").split("\n"):
        if paragraph.strip():
            story.append(Paragraph(paragraph.strip(), body_style))
            story.append(Spacer(1, 0.1 * inch))

    screenshot_base64 = letter.get("screenshot_base64")
    if screenshot_base64:
        story.append(Paragraph("Listing Evidence", section_style))
        image_bytes = base64.b64decode(screenshot_base64)
        image = Image(BytesIO(image_bytes))
        max_width = 5.5 * inch
        if image.drawWidth > max_width:
            scale = max_width / image.drawWidth
            image.drawWidth *= scale
            image.drawHeight *= scale
        story.append(image)

    doc.build(story)
    return buffer.getvalue()
