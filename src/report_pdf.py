"""
Generate a downloadable PDF fit report (used by the web app).

Kept separate from report.py (which generates markdown for the CLI) since
PDF layout logic and markdown layout logic don't share much code.
"""

import io

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)

from .scorer import FitReport


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReqCovered", fontSize=9, leading=13, spaceAfter=6,
        textColor=colors.HexColor("#1a1a1a"),
    ))
    styles.add(ParagraphStyle(
        name="Evidence", fontSize=8, leading=11, spaceAfter=10,
        textColor=colors.HexColor("#555555"), leftIndent=12,
    ))
    styles.add(ParagraphStyle(
        name="MissingMust", fontSize=9, leading=13, spaceAfter=6,
        textColor=colors.HexColor("#b00020"),
    ))
    styles.add(ParagraphStyle(
        name="MissingOther", fontSize=9, leading=13, spaceAfter=6,
        textColor=colors.HexColor("#333333"),
    ))
    return styles


def generate_pdf(report: FitReport, resume_name: str, jd_name: str) -> bytes:
    """Build the PDF report in memory and return raw bytes (nothing written to disk)."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=0.75 * inch, bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch, rightMargin=0.75 * inch,
    )
    styles = _styles()
    story = []

    story.append(Paragraph("Resume Fit Report", styles["Title"]))
    story.append(Paragraph(f"Resume: {resume_name} &nbsp;|&nbsp; JD: {jd_name}",
                            styles["Normal"]))
    story.append(Spacer(1, 16))

    score_table = Table(
        [
            ["Overall Fit Score", f"{report.overall_score * 100:.1f}%"],
            ["Keyword-matched requirements", f"{report.keyword_coverage * 100:.1f}%"],
            ["Semantically-matched requirements", f"{report.semantic_coverage * 100:.1f}%"],
        ],
        colWidths=[3.2 * inch, 2 * inch],
    )
    score_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 20))

    story.append(Paragraph("Missing Requirements (ranked by importance)",
                            styles["Heading2"]))
    missing = report.missing_requirements(top_n=15)
    if not missing:
        story.append(Paragraph("None -- strong coverage.", styles["Normal"]))
    else:
        for r in missing:
            tag = "MUST-HAVE" if r.weight >= 1.5 else (
                "nice-to-have" if r.weight <= 0.6 else "standard"
            )
            style = styles["MissingMust"] if tag == "MUST-HAVE" else styles["MissingOther"]
            story.append(Paragraph(f"[{tag}] {r.requirement}", style))
    story.append(Spacer(1, 16))

    story.append(Paragraph("Covered Requirements (with evidence)", styles["Heading2"]))
    for r in report.covered_requirements():
        story.append(Paragraph(r.requirement, styles["ReqCovered"]))
        detail = f"matched via {r.method} (score {r.score:.2f})"
        if r.evidence:
            detail += f' -- evidence: "{r.evidence}"'
        story.append(Paragraph(detail, styles["Evidence"]))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()