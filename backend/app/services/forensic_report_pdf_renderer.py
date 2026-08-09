"""
TRACE Digital Forensic Examination Report — PDF Renderer.

Generates a professionally formatted forensic investigation report as PDF
using reportlab, following the TRACE framework.
"""

import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.platypus import (
    BaseDocTemplate,
    PageTemplate,
    Frame,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)
from reportlab.platypus.flowables import HRFlowable

BRAND_COLOR = colors.Color(0x1A / 255, 0x23 / 255, 0x7E / 255)
HEADER_BG = colors.Color(0x1A / 255, 0x23 / 255, 0x7E / 255)
LIGHT_BG = colors.Color(0xE8 / 255, 0xEA / 255, 0xF6 / 255)
DARK_BG = colors.Color(0x42 / 255, 0x42 / 255, 0x42 / 255)
PAGE_WIDTH, PAGE_HEIGHT = A4


def _format_date(dt) -> str:
    if isinstance(dt, datetime):
        return dt.strftime("%d/%m/%Y")
    if hasattr(dt, "strftime"):
        return dt.strftime("%d/%m/%Y")
    if dt:
        return str(dt)
    return "---"


def _format_datetime(dt) -> str:
    if isinstance(dt, datetime):
        return dt.strftime("%d/%m/%Y %H:%M IST")
    if dt:
        return str(dt)
    return "---"


def _safe(text: str) -> str:
    if not text:
        return ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _get_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="CoverTitle", parent=styles["Title"],
        fontSize=36, fontName="Helvetica-Bold",
        textColor=BRAND_COLOR, alignment=TA_CENTER, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="CoverSubtitle", parent=styles["Normal"],
        fontSize=20, fontName="Helvetica", alignment=TA_CENTER,
        textColor=colors.Color(0.2, 0.2, 0.2), spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="CoverFIR", parent=styles["Normal"],
        fontSize=14, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="CoverOffense", parent=styles["Normal"],
        fontSize=14, fontName="Helvetica-Oblique", alignment=TA_CENTER, spaceAfter=12,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading", parent=styles["Heading1"],
        fontSize=14, fontName="Helvetica-Bold",
        textColor=BRAND_COLOR, spaceBefore=16, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="SubHeading", parent=styles["Heading2"],
        fontSize=11, fontName="Helvetica-Bold",
        spaceBefore=10, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="Body", parent=styles["Normal"],
        fontSize=10, fontName="Times-Roman", leading=14, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="BodyBold", parent=styles["Normal"],
        fontSize=10, fontName="Times-Bold", leading=14, spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="TOCEntry", parent=styles["Normal"],
        fontSize=11, fontName="Times-Roman", leftIndent=1 * cm, spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        name="SmallBody", parent=styles["Normal"],
        fontSize=9, fontName="Times-Roman", leading=12, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="ItalicNote", parent=styles["Normal"],
        fontSize=10, fontName="Times-Italic", spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="Footer", parent=styles["Normal"],
        fontSize=8, fontName="Times-Italic",
        textColor=colors.Color(0.4, 0.4, 0.4), alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="HeaderMark", parent=styles["Normal"],
        fontSize=8, fontName="Helvetica-Bold",
        textColor=colors.Color(0.8, 0, 0), alignment=TA_CENTER,
    ))

    return styles


def render_forensic_report_pdf(sections_content: dict, case_data: dict, file_path: str):
    """Render the complete TRACE forensic report as PDF."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    styles = _get_styles()

    fir = case_data.get("fir_number", "---")

    def header_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(colors.Color(0.8, 0, 0))
        canvas.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 1.2 * cm,
                                 "CONFIDENTIAL — LAW ENFORCEMENT SENSITIVE")
        canvas.setFont("Times-Italic", 8)
        canvas.setFillColor(colors.Color(0.4, 0.4, 0.4))
        canvas.drawCentredString(PAGE_WIDTH / 2, 1.2 * cm,
                                 f"FIR No. {fir} — TRACE Digital Forensic Examination Report")
        canvas.drawRightString(PAGE_WIDTH - 2.5 * cm, 1.2 * cm, f"Page {doc.page}")
        canvas.restoreState()

    def first_page(canvas, doc):
        pass

    frame = Frame(2.5 * cm, 2.5 * cm, PAGE_WIDTH - 5 * cm, PAGE_HEIGHT - 5 * cm,
                  id="normal")

    doc = BaseDocTemplate(
        file_path,
        pagesize=A4,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
    )
    doc.addPageTemplates([
        PageTemplate(id="First", frames=frame, onPage=first_page),
        PageTemplate(id="Later", frames=frame, onPage=header_footer),
    ])

    story = []

    _render_cover_page(story, case_data, styles)
    story.append(PageBreak())
    story.append(_use_later_template())

    _render_document_control(story, case_data, styles)
    story.append(PageBreak())

    _render_table_of_contents(story, styles)
    story.append(PageBreak())

    # Section 2: Executive Summary
    _render_text_section(story, "2.0", "Executive Summary",
                         sections_content.get("executive_summary", ""), styles)

    # Section 3: Examiner Identity
    story.append(PageBreak())
    _render_examiner_identity(story, case_data, styles)

    # Section 4: Request, Authority, Purpose & Scope
    story.append(PageBreak())
    _render_text_section(story, "4.0", "Request, Authority, Purpose & Scope",
                         sections_content.get("request_authority", ""), styles)

    # Section 5: Information and Assumptions
    _render_text_section(story, "5.0", "Information and Assumptions",
                         sections_content.get("information_assumptions", ""), styles)

    # Section 6: Evidence Integrity Ledger
    story.append(PageBreak())
    _render_evidence_integrity(story, case_data, styles)

    # Section 7: Examination Environment
    _render_examination_environment(story, case_data, styles)

    # Section 8: Methodology
    story.append(PageBreak())
    _render_text_section(story, "8.0", "Methodology",
                         sections_content.get("methodology", ""), styles)

    # Section 9: Time/Date Normalisation
    _render_text_section(story, "9.0", "Time and Date Normalisation",
                         sections_content.get("time_normalisation", ""), styles)

    # Section 10: Findings
    story.append(PageBreak())
    _render_text_section(story, "10.0", "Findings",
                         sections_content.get("findings", ""), styles)

    # Section 11: Consolidated Timeline
    story.append(PageBreak())
    _render_text_section(story, "11.0", "Consolidated Timeline",
                         sections_content.get("consolidated_timeline", ""), styles)

    # Section 12: Responses to Instructions
    story.append(PageBreak())
    _render_text_section(story, "12.0", "Responses to Instructions",
                         sections_content.get("responses_to_instructions", ""), styles)

    # Section 13: IOC Summary
    _render_text_section(story, "13.0", "Indicators of Compromise (IOC) Summary",
                         sections_content.get("ioc_summary", ""), styles)

    # Section 14: Risk Score Matrix
    story.append(PageBreak())
    _render_text_section(story, "14.0", "Risk Score Matrix",
                         sections_content.get("risk_score_matrix", ""), styles)

    # Section 15: Legal Framework
    story.append(PageBreak())
    _render_text_section(story, "15.0", "Legal Framework",
                         sections_content.get("legal_framework", ""), styles)

    # Section 16: Evidentiary Limitations
    _render_text_section(story, "16.0", "Evidentiary Limitations",
                         sections_content.get("evidentiary_limitations", ""), styles)

    # Section 17: Opinions
    story.append(PageBreak())
    _render_text_section(story, "17.0", "Opinions",
                         sections_content.get("opinions", ""), styles)

    # Section 18: Evidence Disposition
    story.append(PageBreak())
    _render_evidence_disposition(story, case_data, styles)

    # Section 19: Statement of Truth
    story.append(PageBreak())
    _render_statement_of_truth(story, case_data, styles)

    # Section 20: Appendices
    story.append(PageBreak())
    _render_appendices(story, case_data, styles)

    doc.build(story)
    return file_path


from reportlab.platypus.flowables import Flowable as _Flowable


class _use_later_template(_Flowable):
    """Flowable that switches to the 'Later' page template."""
    def __init__(self):
        super().__init__()
        self.width = 0
        self.height = 0

    def wrap(self, availWidth, availHeight):
        return (0, 0)

    def draw(self):
        self.canv._doctemplate.handle_nextPageTemplate("Later")


def _render_cover_page(story, case_data, styles):
    story.append(Spacer(1, 4 * cm))
    story.append(Paragraph("TRACE", styles["CoverTitle"]))
    story.append(Paragraph("Digital Forensic Examination Report", styles["CoverSubtitle"]))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(f"FIR No. {_safe(case_data.get('fir_number', '---'))}", styles["CoverFIR"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(_safe(case_data.get("offense_type", "Criminal Investigation")), styles["CoverOffense"]))
    story.append(Spacer(1, 3 * cm))

    metadata = [
        ("Report Reference", f"TRACE/{case_data.get('fir_number', '---')}/{datetime.utcnow().strftime('%Y')}"),
        ("Classification", "CONFIDENTIAL — Law Enforcement Sensitive"),
        ("Prepared By", case_data.get("io_name", "Investigating Officer")),
        ("Date of Report", _format_date(datetime.utcnow())),
        ("Police Station", case_data.get("station_id", "---")),
    ]

    table_data = [
        [Paragraph(f"<b>{_safe(label)}</b>", styles["SmallBody"]),
         Paragraph(_safe(str(value)), styles["SmallBody"])]
        for label, value in metadata
    ]

    t = Table(table_data, colWidths=[5 * cm, 9 * cm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)


def _render_document_control(story, case_data, styles):
    story.append(Paragraph("1.0  Document Control", styles["SectionHeading"]))

    story.append(Paragraph("<b>Version History</b>", styles["Body"]))
    vh_data = [
        [Paragraph("<b>Version</b>", styles["SmallBody"]),
         Paragraph("<b>Date</b>", styles["SmallBody"]),
         Paragraph("<b>Author</b>", styles["SmallBody"]),
         Paragraph("<b>Description</b>", styles["SmallBody"])],
        [Paragraph("1.0", styles["SmallBody"]),
         Paragraph(_format_date(datetime.utcnow()), styles["SmallBody"]),
         Paragraph(_safe(case_data.get("io_name", "IO")), styles["SmallBody"]),
         Paragraph("Initial report", styles["SmallBody"])],
    ]
    t = Table(vh_data, colWidths=[2 * cm, 3 * cm, 4.5 * cm, 4.5 * cm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("<b>Distribution List</b>", styles["Body"]))
    dl_data = [
        [Paragraph("<b>Recipient</b>", styles["SmallBody"]),
         Paragraph("<b>Role</b>", styles["SmallBody"]),
         Paragraph("<b>Classification</b>", styles["SmallBody"])],
        [Paragraph(_safe(case_data.get("io_name", "IO")), styles["SmallBody"]),
         Paragraph("Investigating Officer", styles["SmallBody"]),
         Paragraph("Full Report", styles["SmallBody"])],
        [Paragraph("Court of Competent Jurisdiction", styles["SmallBody"]),
         Paragraph("Judicial Authority", styles["SmallBody"]),
         Paragraph("Full Report", styles["SmallBody"])],
    ]
    t = Table(dl_data, colWidths=[5 * cm, 5 * cm, 4 * cm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(t)


def _render_table_of_contents(story, styles):
    story.append(Paragraph("Table of Contents", styles["SectionHeading"]))

    toc_entries = [
        ("1.0", "Document Control"), ("2.0", "Executive Summary"),
        ("3.0", "Examiner Identity & Qualifications"),
        ("4.0", "Request, Authority, Purpose & Scope"),
        ("5.0", "Information and Assumptions"), ("6.0", "Evidence Integrity Ledger"),
        ("7.0", "Examination Environment"), ("8.0", "Methodology"),
        ("9.0", "Time and Date Normalisation"), ("10.0", "Findings"),
        ("11.0", "Consolidated Timeline"), ("12.0", "Responses to Instructions"),
        ("13.0", "Indicators of Compromise (IOC) Summary"),
        ("14.0", "Risk Score Matrix"), ("15.0", "Legal Framework"),
        ("16.0", "Evidentiary Limitations"), ("17.0", "Opinions"),
        ("18.0", "Evidence Disposition"), ("19.0", "Statement of Truth"),
        ("20.0", "Appendices"),
    ]

    for num, title in toc_entries:
        story.append(Paragraph(f"{num}    {_safe(title)}", styles["TOCEntry"]))


def _render_text_section(story, section_number, title, content, styles):
    story.append(Paragraph(f"{section_number}  {_safe(title)}", styles["SectionHeading"]))

    if not content:
        story.append(Paragraph("<i>[Section content not available]</i>", styles["Body"]))
        return

    paragraphs = content.strip().split("\n")
    for para_text in paragraphs:
        para_text = para_text.strip()
        if not para_text:
            story.append(Spacer(1, 0.2 * cm))
            continue

        if (para_text.endswith(":") and len(para_text) < 80) or (para_text.isupper() and len(para_text) < 60):
            story.append(Paragraph(f"<b>{_safe(para_text)}</b>", styles["Body"]))
            continue

        if len(para_text) > 2 and para_text[0].isdigit() and "." in para_text[:5]:
            parts = para_text.split(" ", 1)
            if len(parts) == 2 and parts[0].replace(".", "").isdigit():
                story.append(Paragraph(f"<b>{_safe(parts[0])}</b> {_safe(parts[1])}", styles["Body"]))
                continue

        story.append(Paragraph(_safe(para_text), styles["Body"]))


def _render_examiner_identity(story, case_data, styles):
    story.append(Paragraph("3.0  Examiner Identity &amp; Qualifications", styles["SectionHeading"]))

    entries = [
        ("Name", case_data.get("io_name", "---")),
        ("Designation", "Investigating Officer"),
        ("Police Station", case_data.get("station_id", "---")),
        ("Badge/ID Number", case_data.get("officer_badge", "---")),
        ("Role in Examination", "Lead Examiner / Investigating Officer"),
    ]

    table_data = [
        [Paragraph(f"<b>{_safe(label)}</b>", styles["SmallBody"]),
         Paragraph(_safe(str(value)), styles["SmallBody"])]
        for label, value in entries
    ]

    t = Table(table_data, colWidths=[5 * cm, 9 * cm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph(
        "The examiner confirms that they have no personal interest in the outcome of this case "
        "and that the opinions expressed in this report are based solely on the evidence examined.",
        styles["Body"]
    ))


def _render_evidence_integrity(story, case_data, styles):
    story.append(Paragraph("6.0  Evidence Integrity Ledger", styles["SectionHeading"]))

    evidence_items = case_data.get("evidence_items", [])
    if not evidence_items:
        story.append(Paragraph("<i>No digital evidence items recorded in the case file.</i>", styles["Body"]))
        return

    headers = ["Exhibit #", "Description", "File Type", "SHA-256 Hash", "Chain of Custody"]
    header_row = [Paragraph(f"<b>{h}</b>", styles["SmallBody"]) for h in headers]
    table_data = [header_row]

    for idx, ev in enumerate(evidence_items):
        hash_val = ev.get("file_hash", "---") or "---"
        short_hash = hash_val[:16] + "..." if len(hash_val) > 16 else hash_val
        custody = ev.get("chain_of_custody", [])
        desc = (ev.get("description") or ev.get("original_filename", "---"))[:50]
        table_data.append([
            Paragraph(f"EX-{idx + 1:03d}", styles["SmallBody"]),
            Paragraph(_safe(desc), styles["SmallBody"]),
            Paragraph(_safe(ev.get("file_type", "---")), styles["SmallBody"]),
            Paragraph(_safe(short_hash), styles["SmallBody"]),
            Paragraph(f"{len(custody)} entries" if custody else "Initial custody", styles["SmallBody"]),
        ])

    col_widths = [2 * cm, 4 * cm, 2.5 * cm, 3.5 * cm, 2.5 * cm]
    t = Table(table_data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)


def _render_examination_environment(story, case_data, styles):
    story.append(Paragraph("7.0  Examination Environment", styles["SectionHeading"]))
    story.append(Paragraph(
        "The examination was conducted using the CrimeGPT Digital Forensic Platform, "
        "an AI-assisted investigation system incorporating multiple forensic analysis modules.",
        styles["Body"]
    ))

    tools = case_data.get("forensic_tools", [])
    if tools:
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph("<b>Forensic Tools Employed:</b>", styles["Body"]))

        headers = ["Tool", "Purpose", "Executions"]
        header_row = [Paragraph(f"<b>{h}</b>", styles["SmallBody"]) for h in headers]
        table_data = [header_row]

        for tool in tools:
            table_data.append([
                Paragraph(_safe(tool.get("name", "---")), styles["SmallBody"]),
                Paragraph(_safe(tool.get("purpose", "---")), styles["SmallBody"]),
                Paragraph(str(tool.get("count", 0)), styles["SmallBody"]),
            ])

        t = Table(table_data, colWidths=[4 * cm, 7 * cm, 2.5 * cm])
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(t)
    else:
        story.append(Paragraph(
            "Standard forensic examination procedures were followed using available platform tools.",
            styles["Body"]
        ))


def _render_evidence_disposition(story, case_data, styles):
    story.append(Paragraph("18.0  Evidence Disposition", styles["SectionHeading"]))

    evidence_items = case_data.get("evidence_items", [])
    story.append(Paragraph(
        "Upon completion of the examination, all evidence items shall be handled as follows:",
        styles["Body"]
    ))

    dispositions = [
        "All original evidence items are to be returned to the custody of the Investigating Officer.",
        "Digital forensic images and working copies are to be retained in secure storage for a minimum period as prescribed by applicable law.",
        "Any temporary files or working copies created during examination have been securely deleted.",
        f"A total of {len(evidence_items)} evidence item(s) were examined during this investigation.",
    ]
    for d in dispositions:
        story.append(Paragraph(f"&bull; {_safe(d)}", styles["Body"]))


def _render_statement_of_truth(story, case_data, styles):
    story.append(Paragraph("19.0  Statement of Truth", styles["SectionHeading"]))

    statements = [
        "I confirm that insofar as the facts stated in this report are within my own knowledge, I have made clear which they are and I believe them to be true, and that the opinions I have expressed represent my true and complete professional opinion.",
        "I understand that proceedings for contempt of court may be brought against anyone who makes, or causes to be made, a false statement in a document verified by a statement of truth without an honest belief in its truth.",
        "I confirm that I have not entered into any arrangement where the amount or payment of my fees is in any way dependent on the outcome of the case.",
        "I have no conflict of interest of any kind, other than any which I have already set out in this report.",
        "I have acted in accordance with the standards of my profession and have complied with relevant legal and procedural requirements.",
    ]
    for s in statements:
        story.append(Paragraph(_safe(s), styles["Body"]))
        story.append(Spacer(1, 0.2 * cm))

    story.append(Spacer(1, 1.5 * cm))
    story.append(HRFlowable(width="40%", thickness=1, color=colors.black))
    story.append(Paragraph(f"<b>{_safe(case_data.get('io_name', 'Investigating Officer'))}</b>", styles["Body"]))
    story.append(Paragraph("Investigating Officer / Digital Forensic Examiner", styles["Body"]))
    story.append(Paragraph(f"Date: {_format_date(datetime.utcnow())}", styles["Body"]))
    story.append(Paragraph(f"Police Station: {_safe(case_data.get('station_id', '---'))}", styles["Body"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("<i>[Official Seal / Stamp]</i>", styles["ItalicNote"]))


def _render_appendices(story, case_data, styles):
    story.append(Paragraph("20.0  Appendices", styles["SectionHeading"]))

    # Appendix A: Evidence Register
    story.append(Paragraph("<b>Appendix A — Evidence Register</b>", styles["SubHeading"]))
    evidence_items = case_data.get("evidence_items", [])
    if evidence_items:
        headers = ["Exhibit #", "Filename", "Type", "Size"]
        header_row = [Paragraph(f"<b>{h}</b>", styles["SmallBody"]) for h in headers]
        table_data = [header_row]
        for idx, ev in enumerate(evidence_items):
            size = ev.get("file_size", 0)
            if size > 1024 * 1024:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} B"
            table_data.append([
                Paragraph(f"EX-{idx + 1:03d}", styles["SmallBody"]),
                Paragraph(_safe((ev.get("original_filename", "---"))[:40]), styles["SmallBody"]),
                Paragraph(_safe(ev.get("file_type", "---")), styles["SmallBody"]),
                Paragraph(size_str, styles["SmallBody"]),
            ])
        t = Table(table_data, colWidths=[2 * cm, 6 * cm, 3 * cm, 3 * cm])
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), DARK_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No evidence items recorded.", styles["Body"]))

    # Appendix B: Forensic Tool Execution Log
    story.append(PageBreak())
    story.append(Paragraph("<b>Appendix B — Forensic Tool Execution Log</b>", styles["SubHeading"]))
    tool_executions = case_data.get("tool_executions", [])
    if tool_executions:
        headers = ["Tool", "Evidence", "Status", "Confidence", "Timestamp"]
        header_row = [Paragraph(f"<b>{h}</b>", styles["SmallBody"]) for h in headers]
        table_data = [header_row]
        for ex in tool_executions[:50]:
            conf = ex.get("confidence")
            conf_str = f"{conf:.0%}" if conf else "---"
            table_data.append([
                Paragraph(_safe(ex.get("tool_name", "---")[:20]), styles["SmallBody"]),
                Paragraph(_safe(ex.get("evidence_name", "---")[:20]), styles["SmallBody"]),
                Paragraph(_safe(ex.get("status", "---")), styles["SmallBody"]),
                Paragraph(conf_str, styles["SmallBody"]),
                Paragraph(_format_datetime(ex.get("created_at")), styles["SmallBody"]),
            ])
        t = Table(table_data, colWidths=[2.5 * cm, 3 * cm, 2.5 * cm, 2.5 * cm, 3.5 * cm])
        t.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), DARK_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No forensic tool executions recorded.", styles["Body"]))

    # Appendix C: Case Diary Summary
    story.append(PageBreak())
    story.append(Paragraph("<b>Appendix C — Case Diary Summary</b>", styles["SubHeading"]))
    diary_entries = case_data.get("diary_entries_list", [])
    if diary_entries:
        for entry in diary_entries:
            story.append(Paragraph(
                f"<b>{_format_date(entry.get('entry_date', ''))} [{_safe(entry.get('entry_type', 'investigation'))}]</b>",
                styles["SmallBody"]
            ))
            story.append(Paragraph(_safe(entry.get("content", "---")[:500]), styles["SmallBody"]))
            story.append(Spacer(1, 0.2 * cm))
    else:
        story.append(Paragraph("No case diary entries recorded.", styles["Body"]))

    # Appendix D: Chain of Custody Records
    story.append(PageBreak())
    story.append(Paragraph("<b>Appendix D — Chain of Custody Records</b>", styles["SubHeading"]))
    has_custody = False
    for ev in evidence_items:
        custody = ev.get("chain_of_custody", [])
        if custody:
            has_custody = True
            story.append(Paragraph(f"<b>Exhibit: {_safe(ev.get('original_filename', '---'))}</b>", styles["Body"]))
            for entry in custody:
                if isinstance(entry, dict):
                    text = f"&bull; {_safe(entry.get('action', '---'))} — {_safe(str(entry.get('timestamp', '---')))} — {_safe(entry.get('officer', '---'))}"
                else:
                    text = f"&bull; {_safe(str(entry))}"
                story.append(Paragraph(text, styles["SmallBody"]))
            story.append(Spacer(1, 0.3 * cm))
    if not has_custody:
        story.append(Paragraph(
            "Chain of custody records are maintained separately in the case management system.",
            styles["Body"]
        ))

    # Appendix E: Glossary
    story.append(PageBreak())
    story.append(Paragraph("<b>Appendix E — Glossary of Terms</b>", styles["SubHeading"]))
    glossary = [
        ("TRACE", "Terms, Record integrity, Analysis, Claims, Exhibits — forensic reporting framework"),
        ("BNS", "Bharatiya Nyaya Sanhita, 2023 — Indian criminal law statute"),
        ("BNSS", "Bharatiya Nagarik Suraksha Sanhita, 2023 — Indian criminal procedure code"),
        ("BSA", "Bharatiya Sakshya Adhiniyam, 2023 — Indian law of evidence"),
        ("IOC", "Indicator of Compromise — forensic artefact suggesting malicious activity"),
        ("SHA-256", "Secure Hash Algorithm producing 256-bit digest for integrity verification"),
        ("S1/S2/S3", "Source Tiers — evidence reliability classification (primary/corroborated/circumstantial)"),
        ("T1/T2/T3", "Temporal Tiers — timestamp reliability classification (authoritative/derived/estimated)"),
        ("FIR", "First Information Report — initial crime report registered with police"),
        ("IO", "Investigating Officer — officer assigned to lead the investigation"),
        ("IST", "Indian Standard Time (UTC+05:30)"),
    ]

    header_row = [
        Paragraph("<b>Term</b>", styles["SmallBody"]),
        Paragraph("<b>Definition</b>", styles["SmallBody"]),
    ]
    table_data = [header_row]
    for term, defn in glossary:
        table_data.append([
            Paragraph(f"<b>{_safe(term)}</b>", styles["SmallBody"]),
            Paragraph(_safe(defn), styles["SmallBody"]),
        ])

    t = Table(table_data, colWidths=[3 * cm, 11 * cm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), DARK_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)
