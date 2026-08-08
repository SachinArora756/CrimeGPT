"""
TRACE Digital Forensic Examination Report — DOCX Renderer.

Generates a professionally formatted 30-40 page forensic investigation report
following the TRACE framework (Terms, Record integrity, Analysis, Claims, Exhibits).
"""

import os
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml


def _set_cell_shading(cell, color: str):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)


def _add_page_break(doc):
    doc.add_page_break()


def _format_datetime(dt) -> str:
    if isinstance(dt, datetime):
        return dt.strftime("%d/%m/%Y %H:%M IST")
    if dt:
        return str(dt)
    return "---"


def _format_date(dt) -> str:
    if isinstance(dt, datetime):
        return dt.strftime("%d/%m/%Y")
    if hasattr(dt, 'strftime'):
        return dt.strftime("%d/%m/%Y")
    if dt:
        return str(dt)
    return "---"


def render_forensic_report(sections_content: dict, case_data: dict, file_path: str):
    """
    Render the complete TRACE forensic report as DOCX.

    Args:
        sections_content: dict mapping section_id -> generated text content
        case_data: dict with all case metadata for data-only sections
        file_path: output file path
    """
    doc = Document()

    _setup_styles(doc)
    _setup_headers_footers(doc, case_data)
    _render_cover_page(doc, case_data)
    _add_page_break(doc)
    _render_document_control(doc, case_data)
    _add_page_break(doc)
    _render_table_of_contents(doc)
    _add_page_break(doc)

    # Section 2: Executive Summary
    _render_text_section(doc, "2.0", "Executive Summary", sections_content.get("executive_summary", ""))

    # Section 3: Examiner Identity
    _add_page_break(doc)
    _render_examiner_identity(doc, case_data)

    # Section 4: Request, Authority, Purpose & Scope
    _add_page_break(doc)
    _render_text_section(doc, "4.0", "Request, Authority, Purpose & Scope", sections_content.get("request_authority", ""))

    # Section 5: Information and Assumptions
    _render_text_section(doc, "5.0", "Information and Assumptions", sections_content.get("information_assumptions", ""))

    # Section 6: Evidence Integrity Ledger
    _add_page_break(doc)
    _render_evidence_integrity(doc, case_data)

    # Section 7: Examination Environment
    _render_examination_environment(doc, case_data)

    # Section 8: Methodology
    _add_page_break(doc)
    _render_text_section(doc, "8.0", "Methodology", sections_content.get("methodology", ""))

    # Section 9: Time/Date Normalisation
    _render_text_section(doc, "9.0", "Time and Date Normalisation", sections_content.get("time_normalisation", ""))

    # Section 10: Findings
    _add_page_break(doc)
    _render_text_section(doc, "10.0", "Findings", sections_content.get("findings", ""))

    # Section 11: Consolidated Timeline
    _add_page_break(doc)
    _render_text_section(doc, "11.0", "Consolidated Timeline", sections_content.get("consolidated_timeline", ""))

    # Section 12: Responses to Instructions
    _add_page_break(doc)
    _render_text_section(doc, "12.0", "Responses to Instructions", sections_content.get("responses_to_instructions", ""))

    # Section 13: IOC Summary
    _render_text_section(doc, "13.0", "Indicators of Compromise (IOC) Summary", sections_content.get("ioc_summary", ""))

    # Section 14: Risk Score Matrix
    _add_page_break(doc)
    _render_text_section(doc, "14.0", "Risk Score Matrix", sections_content.get("risk_score_matrix", ""))

    # Section 15: Legal Framework
    _add_page_break(doc)
    _render_text_section(doc, "15.0", "Legal Framework", sections_content.get("legal_framework", ""))

    # Section 16: Evidentiary Limitations
    _render_text_section(doc, "16.0", "Evidentiary Limitations", sections_content.get("evidentiary_limitations", ""))

    # Section 17: Opinions
    _add_page_break(doc)
    _render_text_section(doc, "17.0", "Opinions", sections_content.get("opinions", ""))

    # Section 18: Evidence Disposition
    _add_page_break(doc)
    _render_evidence_disposition(doc, case_data)

    # Section 19: Statement of Truth
    _add_page_break(doc)
    _render_statement_of_truth(doc, case_data)

    # Section 20: Appendices
    _add_page_break(doc)
    _render_appendices(doc, case_data)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    doc.save(file_path)
    return file_path


def _setup_styles(doc):
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(11)

    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)


def _setup_headers_footers(doc, case_data):
    section = doc.sections[0]
    section.different_first_page_header_footer = True

    header = section.header
    header_para = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
    header_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = header_para.add_run("CONFIDENTIAL — LAW ENFORCEMENT SENSITIVE")
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)
    run.font.bold = True

    footer = section.footer
    footer_para = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
    footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fir = case_data.get("fir_number", "---")
    run = footer_para.add_run(f"FIR No. {fir} — TRACE Digital Forensic Examination Report")
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)


def _render_cover_page(doc, case_data):
    for _ in range(4):
        doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("TRACE")
    run.font.size = Pt(36)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x1A, 0x23, 0x7E)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("Digital Forensic Examination Report")
    run.font.size = Pt(20)
    run.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

    doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(f"FIR No. {case_data.get('fir_number', '---')}")
    run.font.size = Pt(14)
    run.font.bold = True

    doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(case_data.get("offense_type", "Criminal Investigation"))
    run.font.size = Pt(14)
    run.font.italic = True

    for _ in range(4):
        doc.add_paragraph()

    # Cover page metadata table
    table = doc.add_table(rows=5, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    metadata = [
        ("Report Reference", f"TRACE/{case_data.get('fir_number', '---')}/{datetime.utcnow().strftime('%Y')}"),
        ("Classification", "CONFIDENTIAL — Law Enforcement Sensitive"),
        ("Prepared By", case_data.get("io_name", "Investigating Officer")),
        ("Date of Report", _format_date(datetime.utcnow())),
        ("Police Station", case_data.get("station_id", "---")),
    ]

    for i, (label, value) in enumerate(metadata):
        row = table.rows[i]
        cell_label = row.cells[0]
        cell_value = row.cells[1]
        cell_label.text = label
        cell_value.text = value
        _set_cell_shading(cell_label, "E8EAF6")
        for para in cell_label.paragraphs:
            for run in para.runs:
                run.font.bold = True
                run.font.size = Pt(10)
        for para in cell_value.paragraphs:
            for run in para.runs:
                run.font.size = Pt(10)


def _render_document_control(doc, case_data):
    heading = doc.add_heading("1.0  Document Control", level=1)
    heading.runs[0].font.color.rgb = RGBColor(0x1A, 0x23, 0x7E)

    # Version history table
    doc.add_paragraph().add_run("Version History").bold = True
    table = doc.add_table(rows=2, cols=4)
    table.style = 'Table Grid'

    headers = ["Version", "Date", "Author", "Description"]
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        _set_cell_shading(cell, "1A237E")
        for para in cell.paragraphs:
            for run in para.runs:
                run.font.bold = True
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    row = table.rows[1]
    row.cells[0].text = "1.0"
    row.cells[1].text = _format_date(datetime.utcnow())
    row.cells[2].text = case_data.get("io_name", "IO")
    row.cells[3].text = "Initial report"

    doc.add_paragraph()

    # Distribution list
    doc.add_paragraph().add_run("Distribution List").bold = True
    table = doc.add_table(rows=3, cols=3)
    table.style = 'Table Grid'

    headers = ["Recipient", "Role", "Classification"]
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        _set_cell_shading(cell, "1A237E")
        for para in cell.paragraphs:
            for run in para.runs:
                run.font.bold = True
                run.font.size = Pt(9)
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    dist = [
        (case_data.get("io_name", "IO"), "Investigating Officer", "Full Report"),
        ("Court of Competent Jurisdiction", "Judicial Authority", "Full Report"),
    ]
    for i, (name, role, cls) in enumerate(dist):
        row = table.rows[i + 1]
        row.cells[0].text = name
        row.cells[1].text = role
        row.cells[2].text = cls


def _render_table_of_contents(doc):
    heading = doc.add_heading("Table of Contents", level=1)
    heading.runs[0].font.color.rgb = RGBColor(0x1A, 0x23, 0x7E)

    toc_entries = [
        ("1.0", "Document Control"),
        ("2.0", "Executive Summary"),
        ("3.0", "Examiner Identity & Qualifications"),
        ("4.0", "Request, Authority, Purpose & Scope"),
        ("5.0", "Information and Assumptions"),
        ("6.0", "Evidence Integrity Ledger"),
        ("7.0", "Examination Environment"),
        ("8.0", "Methodology"),
        ("9.0", "Time and Date Normalisation"),
        ("10.0", "Findings"),
        ("11.0", "Consolidated Timeline"),
        ("12.0", "Responses to Instructions"),
        ("13.0", "Indicators of Compromise (IOC) Summary"),
        ("14.0", "Risk Score Matrix"),
        ("15.0", "Legal Framework"),
        ("16.0", "Evidentiary Limitations"),
        ("17.0", "Opinions"),
        ("18.0", "Evidence Disposition"),
        ("19.0", "Statement of Truth"),
        ("20.0", "Appendices"),
    ]

    for num, title in toc_entries:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.left_indent = Cm(1)
        run = p.add_run(f"{num}    {title}")
        run.font.size = Pt(11)


def _render_text_section(doc, section_number: str, title: str, content: str):
    heading = doc.add_heading(f"{section_number}  {title}", level=1)
    for run in heading.runs:
        run.font.color.rgb = RGBColor(0x1A, 0x23, 0x7E)

    if not content:
        p = doc.add_paragraph()
        p.add_run("[Section content not available]").italic = True
        return

    paragraphs = content.strip().split("\n")
    for para_text in paragraphs:
        para_text = para_text.strip()
        if not para_text:
            doc.add_paragraph()
            continue

        # Handle sub-headings (lines ending with colon or all-caps short lines)
        if (para_text.endswith(":") and len(para_text) < 80) or (para_text.isupper() and len(para_text) < 60):
            p = doc.add_paragraph()
            run = p.add_run(para_text)
            run.font.bold = True
            run.font.size = Pt(11)
            continue

        # Handle numbered sub-sections (e.g., "10.1", "10.2")
        if len(para_text) > 2 and para_text[0].isdigit() and "." in para_text[:5]:
            parts = para_text.split(" ", 1)
            if len(parts) == 2 and parts[0].replace(".", "").isdigit():
                p = doc.add_paragraph()
                run = p.add_run(parts[0] + " ")
                run.font.bold = True
                p.add_run(parts[1])
                continue

        p = doc.add_paragraph()
        p.add_run(para_text)
        p.paragraph_format.space_after = Pt(6)


def _render_examiner_identity(doc, case_data):
    heading = doc.add_heading("3.0  Examiner Identity & Qualifications", level=1)
    for run in heading.runs:
        run.font.color.rgb = RGBColor(0x1A, 0x23, 0x7E)

    table = doc.add_table(rows=5, cols=2)
    table.style = 'Table Grid'

    entries = [
        ("Name", case_data.get("io_name", "---")),
        ("Designation", "Investigating Officer"),
        ("Police Station", case_data.get("station_id", "---")),
        ("Badge/ID Number", case_data.get("officer_badge", "---")),
        ("Role in Examination", "Lead Examiner / Investigating Officer"),
    ]

    for i, (label, value) in enumerate(entries):
        row = table.rows[i]
        row.cells[0].text = label
        row.cells[1].text = value
        _set_cell_shading(row.cells[0], "E8EAF6")
        for para in row.cells[0].paragraphs:
            for run in para.runs:
                run.font.bold = True
                run.font.size = Pt(10)
        for para in row.cells[1].paragraphs:
            for run in para.runs:
                run.font.size = Pt(10)

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.add_run(
        "The examiner confirms that they have no personal interest in the outcome of this case "
        "and that the opinions expressed in this report are based solely on the evidence examined."
    )
    p.paragraph_format.space_after = Pt(6)


def _render_evidence_integrity(doc, case_data):
    heading = doc.add_heading("6.0  Evidence Integrity Ledger", level=1)
    for run in heading.runs:
        run.font.color.rgb = RGBColor(0x1A, 0x23, 0x7E)

    evidence_items = case_data.get("evidence_items", [])

    if not evidence_items:
        p = doc.add_paragraph()
        p.add_run("No digital evidence items recorded in the case file.").italic = True
        return

    col_count = 5
    table = doc.add_table(rows=1 + len(evidence_items), cols=col_count)
    table.style = 'Table Grid'

    headers = ["Exhibit #", "Description", "File Type", "SHA-256 Hash", "Chain of Custody"]
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = h
        _set_cell_shading(cell, "1A237E")
        for para in cell.paragraphs:
            for run in para.runs:
                run.font.bold = True
                run.font.size = Pt(8)
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for idx, ev in enumerate(evidence_items):
        row = table.rows[idx + 1]
        row.cells[0].text = f"EX-{idx + 1:03d}"
        row.cells[1].text = ev.get("description", ev.get("original_filename", "---"))[:50]
        row.cells[2].text = ev.get("file_type", "---")
        hash_val = ev.get("file_hash", "---")
        row.cells[3].text = hash_val[:16] + "..." if hash_val and len(hash_val) > 16 else (hash_val or "---")
        custody = ev.get("chain_of_custody", [])
        row.cells[4].text = f"{len(custody)} entries" if custody else "Initial custody"

        for cell in row.cells:
            for para in cell.paragraphs:
                for run in para.runs:
                    run.font.size = Pt(8)


def _render_examination_environment(doc, case_data):
    heading = doc.add_heading("7.0  Examination Environment", level=1)
    for run in heading.runs:
        run.font.color.rgb = RGBColor(0x1A, 0x23, 0x7E)

    tools = case_data.get("forensic_tools", [])

    p = doc.add_paragraph()
    p.add_run(
        "The examination was conducted using the CrimeGPT Digital Forensic Platform, "
        "an AI-assisted investigation system incorporating multiple forensic analysis modules."
    )

    if tools:
        doc.add_paragraph()
        doc.add_paragraph().add_run("Forensic Tools Employed:").bold = True

        table = doc.add_table(rows=1 + len(tools), cols=3)
        table.style = 'Table Grid'

        headers = ["Tool", "Purpose", "Executions"]
        for i, h in enumerate(headers):
            cell = table.rows[0].cells[i]
            cell.text = h
            _set_cell_shading(cell, "1A237E")
            for para in cell.paragraphs:
                for run in para.runs:
                    run.font.bold = True
                    run.font.size = Pt(9)
                    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

        for idx, tool in enumerate(tools):
            row = table.rows[idx + 1]
            row.cells[0].text = tool.get("name", "---")
            row.cells[1].text = tool.get("purpose", "---")
            row.cells[2].text = str(tool.get("count", 0))
    else:
        doc.add_paragraph()
        p = doc.add_paragraph()
        p.add_run("Standard forensic examination procedures were followed using available platform tools.")


def _render_evidence_disposition(doc, case_data):
    heading = doc.add_heading("18.0  Evidence Disposition", level=1)
    for run in heading.runs:
        run.font.color.rgb = RGBColor(0x1A, 0x23, 0x7E)

    evidence_items = case_data.get("evidence_items", [])

    p = doc.add_paragraph()
    p.add_run(
        "Upon completion of the examination, all evidence items shall be handled as follows:"
    )

    dispositions = [
        "All original evidence items are to be returned to the custody of the Investigating Officer.",
        "Digital forensic images and working copies are to be retained in secure storage for a minimum period as prescribed by applicable law.",
        "Any temporary files or working copies created during examination have been securely deleted.",
        f"A total of {len(evidence_items)} evidence item(s) were examined during this investigation.",
    ]

    for d in dispositions:
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(1)
        p.add_run(f"• {d}")
        p.paragraph_format.space_after = Pt(4)


def _render_statement_of_truth(doc, case_data):
    heading = doc.add_heading("19.0  Statement of Truth", level=1)
    for run in heading.runs:
        run.font.color.rgb = RGBColor(0x1A, 0x23, 0x7E)

    statements = [
        "I confirm that insofar as the facts stated in this report are within my own knowledge, I have made clear which they are and I believe them to be true, and that the opinions I have expressed represent my true and complete professional opinion.",
        "I understand that proceedings for contempt of court may be brought against anyone who makes, or causes to be made, a false statement in a document verified by a statement of truth without an honest belief in its truth.",
        "I confirm that I have not entered into any arrangement where the amount or payment of my fees is in any way dependent on the outcome of the case.",
        "I have no conflict of interest of any kind, other than any which I have already set out in this report.",
        "I have acted in accordance with the standards of my profession and have complied with relevant legal and procedural requirements.",
    ]

    for s in statements:
        p = doc.add_paragraph()
        p.add_run(s)
        p.paragraph_format.space_after = Pt(8)

    doc.add_paragraph()
    doc.add_paragraph()

    # Signature block
    p = doc.add_paragraph()
    p.add_run("_" * 40)
    p = doc.add_paragraph()
    run = p.add_run(case_data.get("io_name", "Investigating Officer"))
    run.font.bold = True
    p = doc.add_paragraph()
    p.add_run("Investigating Officer / Digital Forensic Examiner")
    p = doc.add_paragraph()
    p.add_run(f"Date: {_format_date(datetime.utcnow())}")
    p = doc.add_paragraph()
    p.add_run(f"Police Station: {case_data.get('station_id', '---')}")

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("[Official Seal / Stamp]")
    run.font.italic = True
    run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)


def _render_appendices(doc, case_data):
    heading = doc.add_heading("20.0  Appendices", level=1)
    for run in heading.runs:
        run.font.color.rgb = RGBColor(0x1A, 0x23, 0x7E)

    # Appendix A: Evidence Register
    doc.add_heading("Appendix A — Evidence Register", level=2)
    evidence_items = case_data.get("evidence_items", [])
    if evidence_items:
        table = doc.add_table(rows=1 + len(evidence_items), cols=4)
        table.style = 'Table Grid'
        headers = ["Exhibit #", "Filename", "Type", "Size"]
        for i, h in enumerate(headers):
            cell = table.rows[0].cells[i]
            cell.text = h
            _set_cell_shading(cell, "424242")
            for para in cell.paragraphs:
                for run in para.runs:
                    run.font.bold = True
                    run.font.size = Pt(9)
                    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        for idx, ev in enumerate(evidence_items):
            row = table.rows[idx + 1]
            row.cells[0].text = f"EX-{idx + 1:03d}"
            row.cells[1].text = ev.get("original_filename", "---")[:40]
            row.cells[2].text = ev.get("file_type", "---")
            size = ev.get("file_size", 0)
            if size > 1024 * 1024:
                row.cells[3].text = f"{size / (1024*1024):.1f} MB"
            elif size > 1024:
                row.cells[3].text = f"{size / 1024:.1f} KB"
            else:
                row.cells[3].text = f"{size} B"
    else:
        doc.add_paragraph("No evidence items recorded.")

    # Appendix B: Forensic Tool Execution Log
    _add_page_break(doc)
    doc.add_heading("Appendix B — Forensic Tool Execution Log", level=2)
    tool_executions = case_data.get("tool_executions", [])
    if tool_executions:
        table = doc.add_table(rows=1 + min(len(tool_executions), 50), cols=5)
        table.style = 'Table Grid'
        headers = ["Tool", "Evidence", "Status", "Confidence", "Timestamp"]
        for i, h in enumerate(headers):
            cell = table.rows[0].cells[i]
            cell.text = h
            _set_cell_shading(cell, "424242")
            for para in cell.paragraphs:
                for run in para.runs:
                    run.font.bold = True
                    run.font.size = Pt(8)
                    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        for idx, ex in enumerate(tool_executions[:50]):
            row = table.rows[idx + 1]
            row.cells[0].text = ex.get("tool_name", "---")[:20]
            row.cells[1].text = ex.get("evidence_name", "---")[:20]
            row.cells[2].text = ex.get("status", "---")
            conf = ex.get("confidence")
            row.cells[3].text = f"{conf:.0%}" if conf else "---"
            row.cells[4].text = _format_datetime(ex.get("created_at"))
            for cell in row.cells:
                for para in cell.paragraphs:
                    for run in para.runs:
                        run.font.size = Pt(8)
    else:
        doc.add_paragraph("No forensic tool executions recorded.")

    # Appendix C: Case Diary Summary
    _add_page_break(doc)
    doc.add_heading("Appendix C — Case Diary Summary", level=2)
    diary_entries = case_data.get("diary_entries", [])
    if diary_entries:
        for entry in diary_entries:
            p = doc.add_paragraph()
            run = p.add_run(f"{_format_date(entry.get('entry_date', ''))} [{entry.get('entry_type', 'investigation')}]")
            run.font.bold = True
            run.font.size = Pt(10)
            p = doc.add_paragraph()
            p.add_run(entry.get("content", "---")[:500])
            p.paragraph_format.space_after = Pt(8)
            p.paragraph_format.left_indent = Cm(0.5)
    else:
        doc.add_paragraph("No case diary entries recorded.")

    # Appendix D: Chain of Custody Records
    _add_page_break(doc)
    doc.add_heading("Appendix D — Chain of Custody Records", level=2)
    has_custody = False
    for ev in evidence_items:
        custody = ev.get("chain_of_custody", [])
        if custody:
            has_custody = True
            p = doc.add_paragraph()
            run = p.add_run(f"Exhibit: {ev.get('original_filename', '---')}")
            run.font.bold = True
            for entry in custody:
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(1)
                if isinstance(entry, dict):
                    p.add_run(f"• {entry.get('action', '---')} — {entry.get('timestamp', '---')} — {entry.get('officer', '---')}")
                else:
                    p.add_run(f"• {str(entry)}")
            doc.add_paragraph()
    if not has_custody:
        doc.add_paragraph("Chain of custody records are maintained separately in the case management system.")

    # Appendix E: Glossary
    _add_page_break(doc)
    doc.add_heading("Appendix E — Glossary of Terms", level=2)
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

    table = doc.add_table(rows=1 + len(glossary), cols=2)
    table.style = 'Table Grid'
    table.rows[0].cells[0].text = "Term"
    table.rows[0].cells[1].text = "Definition"
    _set_cell_shading(table.rows[0].cells[0], "424242")
    _set_cell_shading(table.rows[0].cells[1], "424242")
    for para in table.rows[0].cells[0].paragraphs:
        for run in para.runs:
            run.font.bold = True
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    for para in table.rows[0].cells[1].paragraphs:
        for run in para.runs:
            run.font.bold = True
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for idx, (term, defn) in enumerate(glossary):
        row = table.rows[idx + 1]
        row.cells[0].text = term
        row.cells[1].text = defn
        for para in row.cells[0].paragraphs:
            for run in para.runs:
                run.font.bold = True
                run.font.size = Pt(9)
        for para in row.cells[1].paragraphs:
            for run in para.runs:
                run.font.size = Pt(9)
