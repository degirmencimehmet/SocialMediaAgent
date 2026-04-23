"""
Calendar Export Module — FR-05
Exports monthly content calendar as PDF and JSON.
"""
import json
import logging
from datetime import datetime
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import cm
from sqlalchemy.orm import Session

from database import Post

logger = logging.getLogger(__name__)


def get_monthly_posts(db: Session, tenant_id: str, year: int, month: int) -> list[Post]:
    from sqlalchemy import extract
    return (
        db.query(Post)
        .filter(
            Post.tenant_id == tenant_id,
            Post.status.in_(["approved", "published"]),
            extract("year", Post.post_time) == year,
            extract("month", Post.post_time) == month,
        )
        .order_by(Post.post_time)
        .all()
    )


def export_json(db: Session, tenant_id: str, year: int, month: int) -> dict:
    posts = get_monthly_posts(db, tenant_id, year, month)
    entries = []
    for post in posts:
        entries.append({
            "id": post.id,
            "platform": post.platform,
            "scheduled_time": post.post_time.isoformat() if post.post_time else None,
            "caption_preview": post.caption[:120] + "..." if len(post.caption) > 120 else post.caption,
            "hashtags": post.hashtags_list(),
            "tone": post.tone,
            "status": post.status,
            "image_suggestion": post.image_suggestion,
        })
    return {"month": month, "year": year, "tenant_id": tenant_id, "entries": entries}


def export_pdf(db: Session, tenant_id: str, year: int, month: int) -> bytes:
    posts = get_monthly_posts(db, tenant_id, year, month)
    month_name = datetime(year, month, 1).strftime("%B %Y")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             leftMargin=2*cm, rightMargin=2*cm,
                             topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=16, spaceAfter=12)
    cell_style = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=8, leading=10)

    story = [
        Paragraph(f"📅 Aylık İçerik Takvimi — {month_name}", title_style),
        Paragraph(f"Tenant: {tenant_id}   |   Toplam gönderi: {len(posts)}", styles["Normal"]),
        Spacer(1, 0.5*cm),
    ]

    if not posts:
        story.append(Paragraph("Bu ay için onaylı gönderi bulunamadı.", styles["Normal"]))
    else:
        table_data = [["Tarih & Saat", "Platform", "Önizleme", "Ton", "Durum"]]
        for post in posts:
            date_str = post.post_time.strftime("%d %b\n%H:%M") if post.post_time else "—"
            preview = (post.caption[:100] + "...") if len(post.caption) > 100 else post.caption
            table_data.append([
                Paragraph(date_str, cell_style),
                Paragraph(post.platform.upper(), cell_style),
                Paragraph(preview, cell_style),
                Paragraph(post.tone, cell_style),
                Paragraph(post.status, cell_style),
            ])

        table = Table(table_data, colWidths=[2.5*cm, 2.5*cm, 9*cm, 2*cm, 2*cm])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4F46E5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(table)

    doc.build(story)
    return buffer.getvalue()
