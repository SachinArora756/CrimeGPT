"""
PRISM Digital Forensic Investigation Report — Generation Service.

PRISM: Procedural Record of Investigation, Substantiation & Methodology

Orchestrates the complete forensic report generation:
1. Validates case readiness (status + completeness gating)
2. Aggregates all case data from multiple sources
3. Generates LLM content per section
4. Renders the final DOCX/PDF document
"""

import hashlib
import logging
import os
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm_provider import generate_text
from app.config import settings
from app.models.case import Case, CaseStatus
from app.models.document import Document, DocType, CaseDiary
from app.models.evidence import Evidence
from app.models.forensic_toolkit import ForensicToolExecution
from app.models.investigation_memory import InvestigationMemory, EvidenceCorrelation
from app.models.timeline import TimelineEvent
from app.models.user import User
from app.services.completeness_service import calculate_completeness
from app.services.forensic_report_sections import REPORT_SECTIONS, get_llm_sections
from app.services.forensic_report_renderer import render_forensic_report
from app.services.forensic_report_pdf_renderer import render_forensic_report_pdf

logger = logging.getLogger(__name__)

MINIMUM_COMPLETENESS = 80
ALLOWED_STATUSES = {CaseStatus.CHARGESHEET_FILED, CaseStatus.CLOSED}


async def check_report_readiness(db: AsyncSession, case_id: int) -> dict:
    """Check whether a case is ready for forensic report generation."""
    result = await db.execute(select(Case).where(Case.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    completeness = await calculate_completeness(db, case_id)
    score = completeness["percentage"]

    missing = [
        item["label"] for item in completeness["items"] if not item["completed"]
    ]

    status_ok = case.status in ALLOWED_STATUSES
    score_ok = score >= MINIMUM_COMPLETENESS
    ready = status_ok and score_ok

    if ready:
        message = "Case is ready for forensic report generation."
    elif not status_ok:
        message = (
            f"Case status must be 'chargesheet_filed' or 'closed' before generating a report. "
            f"Current status: {case.status.value}"
        )
    else:
        message = (
            f"Case completeness must be at least {MINIMUM_COMPLETENESS}%. "
            f"Current score: {score}%. Complete the missing items to proceed."
        )

    return {
        "ready": ready,
        "case_status": case.status.value,
        "completeness_score": score,
        "missing_items": missing,
        "message": message,
    }


_generating_cases: dict[int, float] = {}
_GENERATION_TIMEOUT = 300  # 5 minutes max lock


async def generate_forensic_report_doc(
    db: AsyncSession, case_id: int, user_id: int, output_format: str = "pdf"
) -> dict:
    """
    Generate the complete PRISM forensic investigation report.

    Returns dict with document metadata including file_path, file_hash, sections_generated.
    """
    import time

    now = time.time()
    if case_id in _generating_cases:
        elapsed = now - _generating_cases[case_id]
        if elapsed < _GENERATION_TIMEOUT:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Report generation is already in progress for this case. Please wait.",
            )
        else:
            _generating_cases.pop(case_id, None)

    # 1. Validate readiness
    readiness = await check_report_readiness(db, case_id)
    if not readiness["ready"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=readiness["message"],
        )

    _generating_cases[case_id] = time.time()
    try:
        # 2. Load case
        result = await db.execute(select(Case).where(Case.id == case_id))
        case = result.scalar_one()

        # 3. Load officer
        officer_name = "Investigating Officer"
        if case.assigned_officer_id:
            officer_result = await db.execute(
                select(User).where(User.id == case.assigned_officer_id)
            )
            officer = officer_result.scalar_one_or_none()
            if officer:
                officer_name = officer.full_name or officer.email

        # 4. Aggregate all case data
        case_data = await _aggregate_case_data(db, case, officer_name)

        # 5. Generate LLM content for each section
        sections_content = await _generate_all_sections(case_data)

        # 6. Render document
        output_dir = os.path.join(settings.upload_dir, str(case_id), "documents")
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"forensic_report_{timestamp}.{output_format}"
        file_path = os.path.join(output_dir, filename)

        if output_format == "pdf":
            render_forensic_report_pdf(sections_content, case_data, file_path)
        else:
            render_forensic_report(sections_content, case_data, file_path)

        # 7. Compute hash
        file_hash = _compute_file_hash(file_path)

        # 8. Create document record
        doc_record = Document(
            case_id=case_id,
            doc_type=DocType.FORENSIC_REPORT,
            output_format=output_format,
            file_path=file_path,
            file_hash=file_hash,
            generated_by=user_id,
            generated_at=datetime.utcnow(),
        )
        db.add(doc_record)
        await db.commit()
        await db.refresh(doc_record)

        return {
            "id": doc_record.id,
            "case_id": case_id,
            "file_path": file_path,
            "file_hash": file_hash,
            "generated_by": user_id,
            "generated_at": doc_record.generated_at,
            "output_format": output_format,
            "sections_generated": len([s for s in REPORT_SECTIONS if s.is_llm_generated]),
        }
    finally:
        _generating_cases.pop(case_id, None)


async def _aggregate_case_data(db: AsyncSession, case: Case, officer_name: str) -> dict:
    """Pull together all case data needed for the report."""
    case_id = case.id

    # Evidence
    ev_result = await db.execute(
        select(Evidence).where(Evidence.case_id == case_id)
    )
    evidence_list = ev_result.scalars().all()

    # Timeline events
    tl_result = await db.execute(
        select(TimelineEvent)
        .where(TimelineEvent.case_id == case_id)
        .order_by(TimelineEvent.created_at.asc())
    )
    timeline_events = tl_result.scalars().all()

    # Case diary
    diary_result = await db.execute(
        select(CaseDiary)
        .where(CaseDiary.case_id == case_id)
        .order_by(CaseDiary.entry_date.asc())
    )
    diary_entries = diary_result.scalars().all()

    # Forensic tool executions
    tool_result = await db.execute(
        select(ForensicToolExecution)
        .where(ForensicToolExecution.case_id == case_id)
        .order_by(ForensicToolExecution.created_at.asc())
    )
    tool_executions = tool_result.scalars().all()

    # Investigation memory findings
    findings_result = await db.execute(
        select(InvestigationMemory).where(InvestigationMemory.case_id == case_id)
    )
    investigation_findings = findings_result.scalars().all()

    # Evidence correlations
    corr_result = await db.execute(
        select(EvidenceCorrelation).where(EvidenceCorrelation.case_id == case_id)
    )
    correlations = corr_result.scalars().all()

    # Build accused details string
    accused_details = case.accused_name or ""
    if case.accused_persons:
        names = [p.get("name", "") for p in case.accused_persons if isinstance(p, dict)]
        if names:
            accused_details = ", ".join(filter(None, names))

    # Build evidence items list for data-only sections
    evidence_items = []
    for ev in evidence_list:
        evidence_items.append({
            "original_filename": ev.original_filename,
            "file_type": ev.file_type,
            "file_size": ev.file_size,
            "file_hash": ev.file_hash,
            "description": ev.description if hasattr(ev, 'description') else ev.original_filename,
            "chain_of_custody": ev.chain_of_custody or [],
            "ocr_text": ev.ocr_text or "",
            "analysis_results": ev.analysis_results or {},
            "tags": ev.tags or [],
        })

    # Build evidence details text for LLM
    evidence_details = ""
    for i, ev in enumerate(evidence_items):
        evidence_details += f"\nExhibit EX-{i+1:03d}: {ev['original_filename']}\n"
        evidence_details += f"  Type: {ev['file_type']}\n"
        evidence_details += f"  Hash: {ev['file_hash'] or 'Not computed'}\n"
        if ev['ocr_text']:
            evidence_details += f"  OCR Content: {ev['ocr_text'][:500]}\n"
        if ev['analysis_results']:
            evidence_details += f"  Analysis: {_summarize_analysis(ev['analysis_results'])}\n"
        if ev['tags']:
            evidence_details += f"  Tags: {', '.join(ev['tags'])}\n"

    # Build forensic results text
    forensic_results = ""
    for tex in tool_executions:
        if tex.status.value == "completed" and tex.output_data:
            forensic_results += f"\nTool: {tex.tool_key}\n"
            forensic_results += f"  Status: {tex.status.value}\n"
            forensic_results += f"  Confidence: {tex.confidence_score or 'N/A'}\n"
            output_summary = str(tex.output_data)[:300]
            forensic_results += f"  Output: {output_summary}\n"

    # Build investigation findings text
    findings_text = ""
    for finding in investigation_findings:
        findings_text += f"\nFinding [{finding.finding_type}]: {finding.finding_key}\n"
        if finding.finding_data:
            findings_text += f"  Data: {str(finding.finding_data)[:200]}\n"
        if finding.confidence:
            findings_text += f"  Confidence: {finding.confidence:.2f}\n"

    # Build correlations text
    correlations_text = ""
    for corr in correlations:
        correlations_text += (
            f"\nCorrelation: Evidence {corr.source_evidence_id} <-> Evidence {corr.target_evidence_id}\n"
            f"  Type: {corr.correlation_type}, Confidence: {corr.confidence:.2f}\n"
        )
        if corr.details:
            correlations_text += f"  Details: {str(corr.details)[:150]}\n"

    # Build timeline text
    timeline_text = ""
    for ev in timeline_events:
        timeline_text += f"\n{ev.created_at.strftime('%d/%m/%Y %H:%M')} — [{ev.event_type.value}] {ev.title or ''}\n"
        if ev.description:
            timeline_text += f"  {ev.description[:200]}\n"

    # Build diary text
    diary_text = ""
    for entry in diary_entries:
        diary_text += f"\n{entry.entry_date.strftime('%d/%m/%Y')} [{entry.entry_type}]:\n"
        diary_text += f"  {entry.content[:500]}\n"

    # Build tool summary for examination environment
    tool_counts = {}
    for tex in tool_executions:
        key = tex.tool_key
        if key not in tool_counts:
            tool_counts[key] = {"name": key, "purpose": _get_tool_purpose(key), "count": 0}
        tool_counts[key]["count"] += 1

    # Evidence types summary
    evidence_types = set(ev["file_type"] for ev in evidence_items if ev["file_type"])
    evidence_types_summary = ", ".join(evidence_types) if evidence_types else "No evidence types recorded"

    # Key findings summary
    key_findings = case.extracted_data.get("key_facts", []) if case.extracted_data else []
    key_findings_summary = "\n".join(f"- {f}" for f in key_findings) if key_findings else "No key findings extracted"

    # Investigation notes from diary
    investigation_notes = ""
    for entry in diary_entries[:5]:
        investigation_notes += f"{entry.content[:200]}\n"

    # Sections applied as string
    sections_str = ", ".join(case.sections_applied) if case.sections_applied else "None specified"

    return {
        # Case identity
        "fir_number": case.fir_number,
        "case_title": case.title or case.offense_type or "Criminal Investigation",
        "offense_type": case.offense_type or "Not classified",
        "station_id": case.station_id or "---",
        "io_name": officer_name,
        "officer_badge": "---",
        "case_status": case.status.value,
        "case_created_at": case.created_at.strftime("%d/%m/%Y") if case.created_at else "---",

        # Incident details
        "incident_date": case.incident_date.strftime("%d/%m/%Y") if case.incident_date else "---",
        "incident_time": case.incident_time or "---",
        "incident_location": case.incident_location or "---",

        # People
        "complainant_name": case.complainant_name or "---",
        "accused_details": accused_details or "---",

        # Legal
        "sections_applied": sections_str,

        # Case description
        "case_description": case.description or "---",

        # Investigation period
        "investigation_period": _calculate_investigation_period(case),

        # Evidence data
        "evidence_count": len(evidence_items),
        "evidence_items": evidence_items,
        "evidence_details": evidence_details,
        "evidence_types_summary": evidence_types_summary,
        "evidence_summary": evidence_details[:2000],
        "evidence_timestamps": _extract_evidence_timestamps(evidence_items),
        "digital_evidence_summary": evidence_details[:1500],

        # Forensic results
        "forensic_results": forensic_results or "No forensic tool executions recorded.",
        "forensic_tools": list(tool_counts.values()),
        "tool_executions": [
            {
                "tool_name": t.tool_key,
                "evidence_name": f"Evidence #{t.evidence_id}" if t.evidence_id else "N/A",
                "status": t.status.value,
                "confidence": t.confidence_score,
                "created_at": t.created_at,
            }
            for t in tool_executions
        ],
        "tools_used": ", ".join(tool_counts.keys()) if tool_counts else "Standard forensic tools",
        "analysis_techniques": _derive_analysis_techniques(tool_counts),

        # Investigation findings
        "investigation_findings": findings_text or "No automated findings recorded.",
        "correlations": correlations_text or "No cross-evidence correlations identified.",
        "correlation_count": len(correlations),

        # Timeline
        "timeline_events": timeline_text or "No timeline events recorded.",
        "timeline_count": len(timeline_events),

        # Diary (list for renderer, text for LLM prompts)
        "diary_entries": diary_text or "No case diary entries recorded.",
        "diary_entries_list": [
            {
                "entry_date": e.entry_date,
                "entry_type": e.entry_type,
                "content": e.content,
            }
            for e in diary_entries
        ],

        # AI scores
        "risk_score": case.risk_score or 0,
        "ai_confidence": case.ai_confidence or 0,

        # Summaries for LLM prompts
        "key_findings_summary": key_findings_summary,
        "investigation_notes": investigation_notes or "No investigation notes available.",
        "missing_items": ", ".join(
            item["label"]
            for item in (await calculate_completeness(db, case.id))["items"]
            if not item["completed"]
        ) or "None",
    }


def _safe_format(template: str, data: dict) -> str:
    """Format a template string safely, handling curly braces in values.

    Uses string.Template-style replacement to avoid issues with { } in user data.
    Falls back to replacing {key} patterns manually.
    """
    import re

    def replacer(match):
        key = match.group(1)
        if key in data:
            val = data[key]
            return str(val) if val is not None else "---"
        return match.group(0)

    return re.sub(r"\{(\w+)\}", replacer, template)


async def _generate_all_sections(case_data: dict) -> dict:
    """Generate LLM content for all sections that require it."""
    import asyncio

    sections_content = {}
    llm_sections = get_llm_sections()

    for section in llm_sections:
        try:
            prompt = _safe_format(section.prompt_template, case_data)
            content = await asyncio.to_thread(
                generate_text,
                prompt,
                0.3,
                section.max_tokens,
            )
            sections_content[section.section_id] = content
            logger.info(f"Generated section: {section.section_id} ({len(content)} chars)")
        except Exception as e:
            logger.error(f"Error generating section {section.section_id}: {e}", exc_info=True)
            sections_content[section.section_id] = "[Section generation failed due to an error. Manual review required.]"

    return sections_content


def _compute_file_hash(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def _calculate_investigation_period(case: Case) -> str:
    if case.created_at:
        start = case.created_at.strftime("%d/%m/%Y")
        end = datetime.utcnow().strftime("%d/%m/%Y")
        return f"{start} to {end}"
    return "---"


def _extract_evidence_timestamps(evidence_items: list) -> str:
    timestamps = []
    for i, ev in enumerate(evidence_items):
        analysis = ev.get("analysis_results", {})
        if isinstance(analysis, dict):
            ts = analysis.get("timestamp") or analysis.get("created_at")
            if ts:
                timestamps.append(f"EX-{i+1:03d}: {ts}")
    return "\n".join(timestamps) if timestamps else "No specific evidence timestamps extracted."


def _summarize_analysis(analysis: dict) -> str:
    if not isinstance(analysis, dict):
        return str(analysis)[:200]
    parts = []
    for key, value in list(analysis.items())[:5]:
        if isinstance(value, str):
            parts.append(f"{key}: {value[:100]}")
        elif isinstance(value, (int, float)):
            parts.append(f"{key}: {value}")
        elif isinstance(value, list):
            parts.append(f"{key}: [{len(value)} items]")
    return "; ".join(parts) if parts else "No detailed analysis"


def _get_tool_purpose(tool_key: str) -> str:
    purposes = {
        "fingerprint_match": "Fingerprint identification and matching",
        "dna_search": "DNA profile search and comparison",
        "face_detect": "Facial detection in images/video",
        "face_recognize": "Facial recognition against database",
        "vehicle_detect": "Vehicle detection and identification",
        "license_plate_ocr": "License plate recognition",
        "image_object_detect": "Object detection in images",
        "weapon_detect": "Weapon detection in images",
        "digital_hash": "Digital evidence integrity hashing",
        "digital_metadata": "Digital metadata extraction",
        "image_exif": "Image EXIF data extraction",
        "document_pdf_parse": "PDF document parsing",
        "document_ocr": "Document OCR text extraction",
        "image_ocr": "Image text extraction (OCR)",
    }
    return purposes.get(tool_key, "Forensic analysis tool")


def _derive_analysis_techniques(tool_counts: dict) -> str:
    if not tool_counts:
        return "Standard forensic examination procedures"
    techniques = set()
    for key in tool_counts:
        if "fingerprint" in key:
            techniques.add("Fingerprint Analysis")
        elif "dna" in key:
            techniques.add("DNA Profiling")
        elif "face" in key:
            techniques.add("Facial Recognition")
        elif "vehicle" in key or "license" in key:
            techniques.add("Vehicle Identification")
        elif "object" in key or "weapon" in key:
            techniques.add("Object Detection")
        elif "hash" in key or "metadata" in key or "exif" in key:
            techniques.add("Digital Evidence Integrity Verification")
        elif "ocr" in key or "pdf" in key or "document" in key:
            techniques.add("Document Analysis & OCR")
        else:
            techniques.add("Automated Forensic Analysis")
    return ", ".join(sorted(techniques))
