from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib import colors

from app.documents.registry import TemplateDefinition, TemplateSection, SectionType


def render_pdf(template: TemplateDefinition, data: dict, file_path: str):
    doc = SimpleDocTemplate(
        file_path,
        pagesize=A4,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
    )

    styles = _get_styles()
    story = []

    _render_header(story, template, styles)

    for sec in template.sections:
        if sec.section_type == SectionType.METADATA_TABLE:
            _render_metadata_table(story, sec, data, styles)
        elif sec.section_type == SectionType.BODY_TEXT:
            _render_body_text(story, sec, data, styles)
        elif sec.section_type == SectionType.LIST:
            _render_list(story, sec, data, styles)
        elif sec.section_type == SectionType.LEGAL_FOOTER:
            _render_legal_footer(story, sec, data, styles)

    _render_signatures(story, template, styles)
    doc.build(story)


def _get_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="DocTitle",
        parent=styles["Heading1"],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="DocSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        alignment=TA_CENTER,
        fontName="Times-Italic",
        spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="FormNumber",
        parent=styles["Normal"],
        fontSize=9,
        alignment=TA_RIGHT,
        fontName="Times-Italic",
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading",
        parent=styles["Heading2"],
        fontSize=12,
        fontName="Helvetica-Bold",
        spaceBefore=12,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="DocBody",
        parent=styles["Normal"],
        fontSize=10,
        fontName="Times-Roman",
        leading=14,
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="ListItem",
        parent=styles["Normal"],
        fontSize=10,
        fontName="Times-Roman",
        leftIndent=1.5 * cm,
        spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        name="Footer",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Times-Italic",
        spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="Signature",
        parent=styles["Normal"],
        fontSize=10,
        fontName="Times-Roman",
        spaceBefore=24,
    ))

    return styles


def _render_header(story: list, template: TemplateDefinition, styles):
    if template.form_number:
        story.append(Paragraph(template.form_number, styles["FormNumber"]))

    story.append(Paragraph(template.title, styles["DocTitle"]))

    if template.subtitle:
        story.append(Paragraph(template.subtitle, styles["DocSubtitle"]))

    story.append(Spacer(1, 0.5 * cm))


def _render_metadata_table(story: list, section: TemplateSection, data: dict, styles):
    if section.title:
        story.append(Paragraph(section.title, styles["SectionHeading"]))

    table_data = []
    for field_def in section.fields:
        value = data.get(field_def.key, field_def.fallback)
        value_str = str(value) if value else field_def.fallback
        table_data.append([
            Paragraph(f"<b>{field_def.label}</b>", styles["DocBody"]),
            Paragraph(value_str, styles["DocBody"]),
        ])

    if table_data:
        col_widths = [6 * cm, 10 * cm]
        table = Table(table_data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("BACKGROUND", (0, 0), (0, -1), colors.Color(0.95, 0.95, 0.95)),
        ]))
        story.append(table)

    story.append(Spacer(1, 0.3 * cm))


def _render_body_text(story: list, section: TemplateSection, data: dict, styles):
    if section.title:
        story.append(Paragraph(section.title, styles["SectionHeading"]))

    content = data.get(section.content_key, "---") if section.content_key else "---"
    if content and content != "---":
        for para_text in str(content).split("\n"):
            if para_text.strip():
                safe_text = para_text.strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(safe_text, styles["DocBody"]))
    else:
        story.append(Paragraph("---", styles["DocBody"]))

    story.append(Spacer(1, 0.2 * cm))


def _render_list(story: list, section: TemplateSection, data: dict, styles):
    if section.title:
        story.append(Paragraph(section.title, styles["SectionHeading"]))

    items = data.get(section.content_key, []) if section.content_key else []
    if not items:
        story.append(Paragraph("(None)", styles["DocBody"]))
    else:
        for item in items:
            safe = str(item).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(safe, styles["ListItem"]))

    story.append(Spacer(1, 0.2 * cm))


def _render_legal_footer(story: list, section: TemplateSection, data: dict, styles):
    content = data.get(section.content_key, "") if section.content_key else ""
    if content:
        story.append(Spacer(1, 0.3 * cm))
        safe = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        story.append(Paragraph(safe, styles["Footer"]))


def _render_signatures(story: list, template: TemplateDefinition, styles):
    story.append(Spacer(1, 1 * cm))

    for sig in template.signatures:
        story.append(Spacer(1, 0.8 * cm))
        story.append(Paragraph("_" * 50, styles["Signature"]))
        story.append(Paragraph(sig.title, styles["DocBody"]))

        if sig.with_date:
            story.append(Paragraph(
                f"Date: {datetime.utcnow().strftime('%d/%m/%Y')}",
                styles["Footer"]
            ))

        if sig.with_seal:
            story.append(Paragraph("[SEAL]", styles["Footer"]))

    if template.seal_placeholder:
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph("[Official Seal / Stamp]", styles["Footer"]))
