import json

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem
from io import BytesIO


def export_json(report) -> str:
    return json.dumps(
        {
            "title": report.title,
            "overall_confidence": report.overall_confidence,
            "risk_level": report.risk_level,
            "sections": report.sections,
        },
        indent=2,
        default=str,
    )


def _render_value_md(value, indent: int = 0) -> str:
    pad = "  " * indent
    if isinstance(value, str):
        return f"{pad}{value}\n"
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, dict):
                lines.append(f"{pad}- " + ", ".join(f"**{k}**: {v}" for k, v in item.items()))
            else:
                lines.append(f"{pad}- {item}")
        return "\n".join(lines) + "\n"
    if isinstance(value, dict):
        lines = []
        for k, v in value.items():
            lines.append(f"{pad}**{k.replace('_', ' ').title()}**: {v}")
        return "\n".join(lines) + "\n"
    return f"{pad}{value}\n"


def export_markdown(report) -> str:
    lines = [f"# {report.title}", ""]
    lines.append(f"*Overall confidence: {round(report.overall_confidence * 100)}% | Risk level: {report.risk_level}*")
    lines.append("")
    for key, value in report.sections.items():
        heading = key.replace("_", " ").title()
        lines.append(f"## {heading}")
        lines.append(_render_value_md(value))
    return "\n".join(lines)


def export_pdf(report) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Title"], fontSize=20, spaceAfter=12)
    heading_style = ParagraphStyle("HeadingStyle", parent=styles["Heading2"], spaceBefore=14, spaceAfter=6)
    body_style = styles["BodyText"]

    story = [
        Paragraph(report.title, title_style),
        Paragraph(
            f"Overall confidence: {round(report.overall_confidence * 100)}% &nbsp;|&nbsp; Risk level: {report.risk_level}",
            body_style,
        ),
        Spacer(1, 12),
    ]

    for key, value in report.sections.items():
        heading = key.replace("_", " ").title()
        story.append(Paragraph(heading, heading_style))
        if isinstance(value, str):
            story.append(Paragraph(value, body_style))
        elif isinstance(value, list):
            items = []
            for item in value:
                text = ", ".join(f"{k}: {v}" for k, v in item.items()) if isinstance(item, dict) else str(item)
                items.append(ListItem(Paragraph(text, body_style)))
            if items:
                story.append(ListFlowable(items, bulletType="bullet"))
        elif isinstance(value, dict):
            for k, v in value.items():
                story.append(Paragraph(f"<b>{k.replace('_', ' ').title()}</b>: {v}", body_style))
        else:
            story.append(Paragraph(str(value), body_style))

    doc.build(story)
    return buffer.getvalue()
