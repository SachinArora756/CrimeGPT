"""
PRISM Digital Forensic Investigation Report — PDF Renderer.

Generates a professionally formatted forensic investigation report as PDF
using reportlab, following the PRISM framework
(Procedural Record of Investigation, Substantiation & Methodology).
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
from reportlab.platypus.flowables import HRFlowable, Flowable as _Flowable

BRAND_PRIMARY = colors.Color(0x0D / 255, 0x2B / 255, 0x4E / 255)
BRAND_ACCENT = colors.Color(0x1B / 255, 0x5E / 255, 0x8C / 255)
HEADER_BG = colors.Color(0x0D / 255, 0x2B / 255, 0x4E / 255)
LIGHT_BG = colors.Color(0xE3 / 255, 0xEF / 255, 0xF7 / 255)
DARK_BG = colors.Color(0x37 / 255, 0x47 / 255, 0x4F / 255)
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
        fontSize=30, fontName="Helvetica-Bold",
        textColor=BRAND_PRIMARY, alignment=TA_CENTER, spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        name="CoverSubtitle", parent=styles["Normal"],
        fontSize=13, fontName="Helvetica", alignment=TA_CENTER,
        textColor=BRAND_ACCENT, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="CoverFramework", parent=styles["Normal"],
        fontSize=9, fontName="Helvetica-Oblique", alignment=TA_CENTER,
        textColor=colors.Color(0.4, 0.4, 0.4), spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name="CoverFIR", parent=styles["Normal"],
        fontSize=12, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="CoverOffense", parent=styles["Normal"],
        fontSize=11, fontName="Helvetica-Oblique", alignment=TA_CENTER, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="PartHeading", parent=styles["Heading1"],
        fontSize=14, fontName="Helvetica-Bold",
        textColor=BRAND_PRIMARY, spaceBefore=14, spaceAfter=6,
        alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeading", parent=styles["Heading1"],
        fontSize=11, fontName="Helvetica-Bold",
        textColor=BRAND_PRIMARY, spaceBefore=10, spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        name="SubHeading", parent=styles["Heading2"],
        fontSize=10, fontName="Helvetica-Bold",
        spaceBefore=8, spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        name="Body", parent=styles["Normal"],
        fontSize=9, fontName="Times-Roman", leading=12, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="BodyBold", parent=styles["Normal"],
        fontSize=9, fontName="Times-Bold", leading=12, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="TOCEntry", parent=styles["Normal"],
        fontSize=10, fontName="Times-Roman", leftIndent=1 * cm, spaceAfter=2,
    ))
    styles.add(ParagraphStyle(
        name="TOCPart", parent=styles["Normal"],
        fontSize=10, fontName="Helvetica-Bold", leftIndent=0.3 * cm,
        spaceAfter=2, spaceBefore=6, textColor=BRAND_ACCENT,
    ))
    styles.add(ParagraphStyle(
        name="SmallBody", parent=styles["Normal"],
        fontSize=8, fontName="Times-Roman", leading=10, spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        name="ItalicNote", parent=styles["Normal"],
        fontSize=9, fontName="Times-Italic", spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="Footer", parent=styles["Normal"],
        fontSize=7, fontName="Times-Italic",
        textColor=colors.Color(0.4, 0.4, 0.4), alignment=TA_CENTER,
    ))

    return styles


def render_forensic_report_pdf(sections_content: dict, case_data: dict, file_path: str):
    """Render the complete PRISM forensic report as PDF."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    styles = _get_styles()

    fir = case_data.get("fir_number", "---")

    def header_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica-Bold", 7)
        canvas.setFillColor(colors.Color(0.7, 0, 0))
        canvas.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 1.0 * cm,
                                 "RESTRICTED — FOR AUTHORIZED LAW ENFORCEMENT USE ONLY")
        canvas.setFont("Times-Italic", 7)
        canvas.setFillColor(colors.Color(0.4, 0.4, 0.4))
        canvas.drawCentredString(PAGE_WIDTH / 2, 1.0 * cm,
                                 f"FIR No. {fir} — PRISM Forensic Investigation Report")
        canvas.drawRightString(PAGE_WIDTH - 2.0 * cm, 1.0 * cm, f"Page {doc.page}")
        canvas.restoreState()

    def first_page(canvas, doc):
        pass

    frame = Frame(2.0 * cm, 2.0 * cm, PAGE_WIDTH - 4 * cm, PAGE_HEIGHT - 4 * cm,
                  id="normal")

    doc = BaseDocTemplate(
        file_path,
        pagesize=A4,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
    )
    doc.addPageTemplates([
        PageTemplate(id="First", frames=frame, onPage=first_page),
        PageTemplate(id="Later", frames=frame, onPage=header_footer),
    ])

    story = []

    # Cover page
    _render_cover_page(story, case_data, styles)
    story.append(PageBreak())
    story.append(_UseLaterTemplate())

    # Document Administration
    _render_document_administration(story, case_data, styles)
    story.append(PageBreak())

    # Table of Contents
    _render_table_of_contents(story, styles)
    story.append(PageBreak())

    # ─── PART I: PROVENANCE ───────────────────────────
    story.append(Paragraph("PART I — PROVENANCE", styles["PartHeading"]))
    story.append(Spacer(1, 0.2 * cm))

    # Section 2: Investigation Mandate & Authority
    _render_text_section(story, "2.0", "Investigation Mandate &amp; Authority",
                         sections_content.get("mandate_authority", ""), styles)

    # Section 3: Examiner Declaration
    _render_examiner_declaration(story, case_data, styles)

    # ─── PART II: RECONSTRUCTION ──────────────────────
    story.append(PageBreak())
    story.append(Paragraph("PART II — RECONSTRUCTION", styles["PartHeading"]))
    story.append(Spacer(1, 0.2 * cm))

    # Section 4: Case Synopsis
    _render_text_section(story, "4.0", "Case Synopsis",
                         sections_content.get("case_synopsis", ""), styles)

    # Section 5: Evidence Inventory
    _render_evidence_inventory(story, case_data, styles)

    # Section 6: Technical Infrastructure
    _render_technical_infrastructure(story, case_data, styles)

    # Section 7: Analytical Protocol
    _render_text_section(story, "7.0", "Analytical Protocol",
                         sections_content.get("analytical_protocol", ""), styles)

    # Section 8: Temporal Framework
    _render_text_section(story, "8.0", "Temporal Synchronization Framework",
                         sections_content.get("temporal_framework", ""), styles)

    # Section 9: Examination Findings
    story.append(PageBreak())
    _render_text_section(story, "9.0", "Detailed Examination Findings",
                         sections_content.get("examination_findings", ""), styles)

    # Section 10: Event Reconstruction
    story.append(PageBreak())
    _render_text_section(story, "10.0", "Chronological Event Reconstruction",
                         sections_content.get("event_reconstruction", ""), styles)

    # ─── PART III: INTERPRETATION ─────────────────────
    story.append(PageBreak())
    story.append(Paragraph("PART III — INTERPRETATION", styles["PartHeading"]))
    story.append(Spacer(1, 0.2 * cm))

    # Section 11: Investigative Conclusions
    _render_text_section(story, "11.0", "Investigative Conclusions",
                         sections_content.get("investigative_conclusions", ""), styles)

    # Section 12: Digital Threat Assessment
    _render_text_section(story, "12.0", "Digital Threat Assessment",
                         sections_content.get("threat_assessment", ""), styles)

    # Section 13: Evidence Strength Evaluation
    _render_text_section(story, "13.0", "Evidence Strength Evaluation",
                         sections_content.get("strength_evaluation", ""), styles)

    # ─── PART IV: SUBSTANTIATION ──────────────────────
    story.append(PageBreak())
    story.append(Paragraph("PART IV — SUBSTANTIATION", styles["PartHeading"]))
    story.append(Spacer(1, 0.2 * cm))

    # Section 14: Legal Compliance
    _render_text_section(story, "14.0", "Legal Compliance Framework",
                         sections_content.get("legal_compliance", ""), styles)

    # Section 15: Methodological Constraints
    _render_text_section(story, "15.0", "Methodological Constraints &amp; Limitations",
                         sections_content.get("methodological_constraints", ""), styles)

    # Section 16: Preliminary Information
    _render_text_section(story, "16.0", "Preliminary Information &amp; Working Hypotheses",
                         sections_content.get("preliminary_information", ""), styles)

    # ─── PART V: MEMORANDUM ───────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("PART V — MEMORANDUM", styles["PartHeading"]))
    story.append(Spacer(1, 0.2 * cm))

    # Section 17: Expert Opinion
    _render_text_section(story, "17.0", "Expert Professional Opinion",
                         sections_content.get("professional_opinion", ""), styles)

    # Section 18: Evidence Disposition
    story.append(PageBreak())
    _render_evidence_disposition(story, case_data, styles)

    # Section 19: Declaration & Attestation
    story.append(PageBreak())
    _render_declaration_attestation(story, case_data, styles)

    # Section 20: Annexures
    story.append(PageBreak())
    _render_annexures(story, case_data, styles)

    doc.build(story)
    return file_path


class _UseLaterTemplate(_Flowable):
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
    story.append(Spacer(1, 2.5 * cm))
    story.append(Paragraph("PRISM", styles["CoverTitle"]))
    story.append(Paragraph("Digital Forensic Investigation Report", styles["CoverSubtitle"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        "Procedural Record of Investigation, Substantiation &amp; Methodology",
        styles["CoverFramework"]
    ))
    story.append(Spacer(1, 0.8 * cm))
    story.append(Paragraph(f"FIR No. {_safe(case_data.get('fir_number', '---'))}", styles["CoverFIR"]))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(_safe(case_data.get("offense_type", "Criminal Investigation")), styles["CoverOffense"]))
    story.append(Spacer(1, 2 * cm))

    metadata = [
        ("Report Reference", f"PRISM/{case_data.get('fir_number', '---')}/{datetime.utcnow().strftime('%Y')}"),
        ("Security Classification", "RESTRICTED — For Authorized Law Enforcement Use Only"),
        ("Prepared By", case_data.get("io_name", "Investigating Officer")),
        ("Date of Compilation", _format_date(datetime.utcnow())),
        ("Originating Station", case_data.get("station_id", "---")),
        ("Framework Version", "PRISM v1.0"),
    ]

    table_data = [
        [Paragraph(f"<b>{_safe(label)}</b>", styles["SmallBody"]),
         Paragraph(_safe(str(value)), styles["SmallBody"])]
        for label, value in metadata
    ]

    t = Table(table_data, colWidths=[5 * cm, 10 * cm])
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.Color(0.6, 0.6, 0.6)),
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)


def _render_document_administration(story, case_data, styles):
    story.append(Paragraph("1.0  Document Administration", styles["SectionHeading"]))

    story.append(Paragraph("<b>Revision Record</b>", styles["Body"]))
    vh_data = [
        [Paragraph("<b>Rev.</b>", styles["SmallBody"]),
         Paragraph("<b>Date</b>", styles["SmallBody"]),
         Paragraph("<b>Prepared By</b>", styles["SmallBody"]),
         Paragraph("<b>Nature of Revision</b>", styles["SmallBody"])],
        [Paragraph("1.0", styles["SmallBody"]),
         Paragraph(_format_date(datetime.utcnow()), styles["SmallBody"]),
         Paragraph(_safe(case_data.get("io_name", "IO")), styles["SmallBody"]),
         Paragraph("Original compilation", styles["SmallBody"])],
    ]
    t = Table(vh_data, colWidths=[1.5 * cm, 3 * cm, 5 * cm, 4.5 * cm])
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

    story.append(Paragraph("<b>Authorized Recipients</b>", styles["Body"]))
    dl_data = [
        [Paragraph("<b>Recipient</b>", styles["SmallBody"]),
         Paragraph("<b>Designation</b>", styles["SmallBody"]),
         Paragraph("<b>Access Level</b>", styles["SmallBody"])],
        [Paragraph(_safe(case_data.get("io_name", "IO")), styles["SmallBody"]),
         Paragraph("Investigating Officer", styles["SmallBody"]),
         Paragraph("Full Report", styles["SmallBody"])],
        [Paragraph("Competent Court", styles["SmallBody"]),
         Paragraph("Judicial Authority", styles["SmallBody"]),
         Paragraph("Full Report", styles["SmallBody"])],
        [Paragraph("Supervisory Officer", styles["SmallBody"]),
         Paragraph("SHO / SP Office", styles["SmallBody"]),
         Paragraph("Executive Summary", styles["SmallBody"])],
    ]
    t = Table(dl_data, colWidths=[5 * cm, 4.5 * cm, 4.5 * cm])
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

    toc = [
        (None, "PART I — PROVENANCE"),
        ("1.0", "Document Administration"),
        ("2.0", "Investigation Mandate & Authority"),
        ("3.0", "Examiner Declaration & Credentials"),
        (None, "PART II — RECONSTRUCTION"),
        ("4.0", "Case Synopsis"),
        ("5.0", "Evidence Inventory & Integrity Verification"),
        ("6.0", "Technical Infrastructure & Instruments"),
        ("7.0", "Analytical Protocol"),
        ("8.0", "Temporal Synchronization Framework"),
        ("9.0", "Detailed Examination Findings"),
        ("10.0", "Chronological Event Reconstruction"),
        (None, "PART III — INTERPRETATION"),
        ("11.0", "Investigative Conclusions"),
        ("12.0", "Digital Threat Assessment"),
        ("13.0", "Evidence Strength Evaluation"),
        (None, "PART IV — SUBSTANTIATION"),
        ("14.0", "Legal Compliance Framework"),
        ("15.0", "Methodological Constraints & Limitations"),
        ("16.0", "Preliminary Information & Working Hypotheses"),
        (None, "PART V — MEMORANDUM"),
        ("17.0", "Expert Professional Opinion"),
        ("18.0", "Evidence Handling & Disposition"),
        ("19.0", "Declaration & Attestation"),
        ("20.0", "Supporting Annexures"),
    ]

    for num, title in toc:
        if num is None:
            story.append(Paragraph(_safe(title), styles["TOCPart"]))
        else:
            story.append(Paragraph(f"{num}    {_safe(title)}", styles["TOCEntry"]))


def _render_text_section(story, section_number, title, content, styles):
    story.append(Paragraph(f"{section_number}  {title}", styles["SectionHeading"]))

    if not content:
        story.append(Paragraph("<i>[Section content pending generation]</i>", styles["Body"]))
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


def _render_examiner_declaration(story, case_data, styles):
    story.append(Paragraph("3.0  Examiner Declaration &amp; Credentials", styles["SectionHeading"]))

    entries = [
        ("Name", case_data.get("io_name", "---")),
        ("Designation", "Investigating Officer / Digital Forensic Examiner"),
        ("Originating Station", case_data.get("station_id", "---")),
        ("Identification No.", case_data.get("officer_badge", "---")),
        ("Role in Investigation", "Lead Examiner"),
        ("Declaration Date", _format_date(datetime.utcnow())),
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
        "The undersigned hereby declares that they have no personal, financial, or other interest "
        "in the outcome of this case. The findings and opinions expressed herein are based solely "
        "upon the evidence examined and the professional expertise of the examiner. This declaration "
        "is made in compliance with the requirements of the Bharatiya Sakshya Adhiniyam, 2023.",
        styles["Body"]
    ))


def _render_evidence_inventory(story, case_data, styles):
    story.append(Paragraph("5.0  Evidence Inventory &amp; Integrity Verification", styles["SectionHeading"]))

    evidence_items = case_data.get("evidence_items", [])
    if not evidence_items:
        story.append(Paragraph("<i>No evidence items recorded in the case management system.</i>", styles["Body"]))
        return

    story.append(Paragraph(
        f"A total of {len(evidence_items)} evidence item(s) were received, catalogued, "
        "and subjected to integrity verification. The following register documents each item:",
        styles["Body"]
    ))
    story.append(Spacer(1, 0.2 * cm))

    headers = ["Exhibit", "Description", "Format", "Integrity Hash (SHA-256)", "Provenance"]
    header_row = [Paragraph(f"<b>{h}</b>", styles["SmallBody"]) for h in headers]
    table_data = [header_row]

    for idx, ev in enumerate(evidence_items):
        hash_val = ev.get("file_hash", "---") or "---"
        short_hash = hash_val[:16] + "..." if len(hash_val) > 16 else hash_val
        custody = ev.get("chain_of_custody", [])
        desc = (ev.get("description") or ev.get("original_filename", "---"))[:45]
        table_data.append([
            Paragraph(f"EX-{idx + 1:03d}", styles["SmallBody"]),
            Paragraph(_safe(desc), styles["SmallBody"]),
            Paragraph(_safe(ev.get("file_type", "---")), styles["SmallBody"]),
            Paragraph(_safe(short_hash), styles["SmallBody"]),
            Paragraph(f"{len(custody)} transfer(s)" if custody else "Original receipt", styles["SmallBody"]),
        ])

    col_widths = [1.8 * cm, 4 * cm, 2.2 * cm, 3.5 * cm, 2.5 * cm]
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


def _render_technical_infrastructure(story, case_data, styles):
    story.append(Paragraph("6.0  Technical Infrastructure &amp; Instruments", styles["SectionHeading"]))
    story.append(Paragraph(
        "The forensic examination was conducted utilizing the CrimeGPT Digital Forensic Platform, "
        "an integrated AI-assisted investigation system incorporating specialized forensic analysis modules. "
        "The platform maintains audit trails for all analytical operations performed.",
        styles["Body"]
    ))

    tools = case_data.get("forensic_tools", [])
    if tools:
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph("<b>Instruments &amp; Analytical Modules Employed:</b>", styles["Body"]))

        headers = ["Module", "Function", "Invocations"]
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
            "Standard forensic examination procedures were followed using the platform's built-in analytical capabilities.",
            styles["Body"]
        ))


def _render_evidence_disposition(story, case_data, styles):
    story.append(Paragraph("18.0  Evidence Handling &amp; Disposition", styles["SectionHeading"]))

    evidence_items = case_data.get("evidence_items", [])
    story.append(Paragraph(
        "Upon completion of the forensic examination, all evidence items are subject to the following disposition protocol:",
        styles["Body"]
    ))

    dispositions = [
        "All original evidence items shall be returned to the custody of the designated Investigating Officer under documented transfer.",
        "Forensic images, working copies, and derivative materials shall be retained in secure encrypted storage for the legally prescribed retention period.",
        "All temporary files, intermediate outputs, and working copies created during the examination have been securely purged using certified deletion procedures.",
        f"This examination processed a total of {len(evidence_items)} evidence item(s) as documented in the Evidence Inventory (Section 5.0).",
        "The integrity of all evidence items was verified both at receipt and upon return, with hash values confirmed unchanged.",
    ]
    for d in dispositions:
        story.append(Paragraph(f"&bull; {_safe(d)}", styles["Body"]))


def _render_declaration_attestation(story, case_data, styles):
    story.append(Paragraph("19.0  Declaration &amp; Attestation", styles["SectionHeading"]))

    story.append(Paragraph(
        "The undersigned solemnly declares and attests as follows:",
        styles["Body"]
    ))
    story.append(Spacer(1, 0.2 * cm))

    statements = [
        "I confirm that the facts stated in this report, insofar as they are within my personal knowledge, are true and accurate to the best of my belief. Where facts are based upon information provided by others, I have identified the source and believe such information to be reliable.",
        "The professional opinions expressed in this report represent my genuine, considered assessment based solely upon the evidence examined, the analytical procedures applied, and my professional training and experience.",
        "I understand that this report may be submitted to a court of law and that I may be called upon to give evidence in relation to its contents. I am aware of the consequences of making a false declaration.",
        "I confirm that no arrangement exists, nor has been entered into, whereby my remuneration or any benefit is contingent upon the findings or outcome of this case.",
        "I have no conflict of interest, financial or otherwise, in relation to any party to these proceedings, except as may be disclosed elsewhere in this report.",
        "The examination was conducted in accordance with established forensic science principles, applicable professional standards, and the procedural requirements of Indian law.",
    ]
    for i, s in enumerate(statements):
        story.append(Paragraph(f"{i+1}. {_safe(s)}", styles["Body"]))
        story.append(Spacer(1, 0.15 * cm))

    story.append(Spacer(1, 1.0 * cm))
    story.append(HRFlowable(width="40%", thickness=1, color=colors.black))
    story.append(Paragraph(f"<b>{_safe(case_data.get('io_name', 'Investigating Officer'))}</b>", styles["Body"]))
    story.append(Paragraph("Investigating Officer / Digital Forensic Examiner", styles["Body"]))
    story.append(Paragraph(f"Date: {_format_date(datetime.utcnow())}", styles["Body"]))
    story.append(Paragraph(f"Station: {_safe(case_data.get('station_id', '---'))}", styles["Body"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("<i>[Official Seal / Stamp]</i>", styles["ItalicNote"]))


def _render_annexures(story, case_data, styles):
    story.append(Paragraph("20.0  Supporting Annexures", styles["SectionHeading"]))

    # Annexure A: Complete Evidence Register
    story.append(Paragraph("<b>Annexure A — Complete Evidence Register</b>", styles["SubHeading"]))
    evidence_items = case_data.get("evidence_items", [])
    if evidence_items:
        headers = ["Exhibit", "Filename", "Format", "Size"]
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

    # Annexure B: Forensic Module Execution Log
    story.append(PageBreak())
    story.append(Paragraph("<b>Annexure B — Forensic Module Execution Log</b>", styles["SubHeading"]))
    tool_executions = case_data.get("tool_executions", [])
    if tool_executions:
        headers = ["Module", "Target", "Result", "Confidence", "Timestamp"]
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
        story.append(Paragraph("No forensic module executions recorded.", styles["Body"]))

    # Annexure C: Investigation Diary Summary
    story.append(PageBreak())
    story.append(Paragraph("<b>Annexure C — Investigation Diary Summary</b>", styles["SubHeading"]))
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
        story.append(Paragraph("No investigation diary entries recorded.", styles["Body"]))

    # Annexure D: Provenance Chain Records
    story.append(PageBreak())
    story.append(Paragraph("<b>Annexure D — Provenance Chain Records</b>", styles["SubHeading"]))
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
            story.append(Spacer(1, 0.2 * cm))
    if not has_custody:
        story.append(Paragraph(
            "Provenance chain records are maintained within the case management system and are available upon request.",
            styles["Body"]
        ))

    # Annexure E: Terminology Reference
    story.append(PageBreak())
    story.append(Paragraph("<b>Annexure E — Terminology Reference</b>", styles["SubHeading"]))
    glossary = [
        ("PRISM", "Procedural Record of Investigation, Substantiation & Methodology — forensic reporting framework"),
        ("Grade Alpha", "Direct primary evidence from original source — highest evidentiary weight"),
        ("Grade Beta", "Corroborated evidence supported by secondary sources"),
        ("Grade Gamma", "Circumstantial or indirect evidence requiring further substantiation"),
        ("Temporal Verified", "Timestamp from authoritative/system source — highest temporal reliability"),
        ("Temporal Derived", "Computed or calculated timestamp from available data"),
        ("Temporal Estimated", "Approximate time based on contextual indicators"),
        ("BNS", "Bharatiya Nyaya Sanhita, 2023 — Indian substantive criminal law"),
        ("BNSS", "Bharatiya Nagarik Suraksha Sanhita, 2023 — Indian criminal procedure code"),
        ("BSA", "Bharatiya Sakshya Adhiniyam, 2023 — Indian law of evidence"),
        ("FIR", "First Information Report — initial crime report registered with police"),
        ("IO", "Investigating Officer — officer assigned to lead the investigation"),
        ("IST", "Indian Standard Time (UTC+05:30)"),
        ("SHA-256", "Secure Hash Algorithm producing 256-bit digest for integrity verification"),
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

    t = Table(table_data, colWidths=[3.5 * cm, 10.5 * cm])
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
