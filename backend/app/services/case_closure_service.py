"""Case Closure Verification Service - ensures all investigation steps are completed."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, exists

from app.models.forensic_toolkit import ForensicToolExecution, ExecutionStatus
from app.models.evidence import Evidence
from app.models.case import Case

logger = logging.getLogger(__name__)

CLOSURE_CHECKLIST = [
    {
        "key": "fingerprint_searched",
        "label": "Fingerprints searched in database",
        "tools": ["fingerprint_match"],
        "weight": 15,
    },
    {
        "key": "dna_searched",
        "label": "DNA searched in database",
        "tools": ["dna_search"],
        "weight": 15,
    },
    {
        "key": "vehicle_searched",
        "label": "Vehicles searched and identified",
        "tools": ["vehicle_detect", "license_plate_ocr"],
        "weight": 10,
    },
    {
        "key": "cctv_checked",
        "label": "CCTV/video evidence analyzed",
        "tools": ["image_object_detect", "face_detect"],
        "evidence_type": "video",
        "weight": 10,
    },
    {
        "key": "face_searched",
        "label": "Face recognition against criminal database",
        "tools": ["face_recognize"],
        "weight": 15,
    },
    {
        "key": "previous_fir_checked",
        "label": "Previous FIRs/cases cross-referenced",
        "tools": ["face_recognize", "fingerprint_match", "dna_search"],
        "weight": 10,
    },
    {
        "key": "digital_evidence",
        "label": "Digital evidence (metadata, hashes) preserved",
        "tools": ["digital_hash", "digital_metadata", "image_exif"],
        "weight": 10,
    },
    {
        "key": "documents_analyzed",
        "label": "Documents analyzed and OCR extracted",
        "tools": ["document_pdf_parse", "document_ocr", "image_ocr"],
        "weight": 5,
    },
    {
        "key": "weapons_checked",
        "label": "Weapon detection performed",
        "tools": ["weapon_detect"],
        "weight": 5,
    },
    {
        "key": "evidence_integrity",
        "label": "Evidence integrity verified (hashes computed)",
        "tools": ["digital_hash"],
        "weight": 5,
    },
]


async def verify_case_closure_readiness(case_id: int, db: AsyncSession) -> dict:
    """Verify all investigation steps are completed before case closure."""
    evidence_stmt = select(Evidence).where(Evidence.case_id == case_id)
    evidence_result = await db.execute(evidence_stmt)
    evidence_items = evidence_result.scalars().all()

    if not evidence_items:
        return {
            "ready": False,
            "checklist": [],
            "warnings": ["No evidence has been uploaded for this case."],
            "completion_percentage": 0.0,
        }

    exec_stmt = (
        select(ForensicToolExecution.tool_key, func.count(ForensicToolExecution.id))
        .where(ForensicToolExecution.case_id == case_id)
        .where(ForensicToolExecution.status == ExecutionStatus.COMPLETED)
        .group_by(ForensicToolExecution.tool_key)
    )
    exec_result = await db.execute(exec_stmt)
    completed_tools = dict(exec_result.all())

    evidence_types = set(e.file_type for e in evidence_items if e.file_type)
    has_images = any(t in ("image", "image/jpeg", "image/png") for t in evidence_types)
    has_documents = any(t in ("document", "application/pdf") for t in evidence_types)

    checklist = []
    total_weight = 0
    achieved_weight = 0
    warnings = []

    for item_def in CLOSURE_CHECKLIST:
        required_tools = item_def["tools"]
        weight = item_def["weight"]

        if "evidence_type" in item_def:
            req_type = item_def["evidence_type"]
            if req_type == "video" and "video" not in str(evidence_types):
                checklist.append({
                    "key": item_def["key"],
                    "label": item_def["label"],
                    "status": "not_applicable",
                    "details": "No video evidence in this case",
                })
                continue

        total_weight += weight

        executed_count = sum(completed_tools.get(t, 0) for t in required_tools)

        if executed_count > 0:
            status = "completed"
            details = f"Executed {executed_count} time(s)"
            achieved_weight += weight
        elif not has_images and all(t not in ("digital_hash", "document_pdf_parse", "document_ocr", "dna_search") for t in required_tools):
            status = "not_applicable"
            details = "No image evidence requiring this analysis"
            total_weight -= weight
        else:
            status = "missing"
            details = "Not yet performed"
            warnings.append(f"WARNING: {item_def['label']} has not been completed")

    completion_percentage = (achieved_weight / max(total_weight, 1)) * 100

    ready = completion_percentage >= 70 and len(warnings) <= 2

    if not ready and completion_percentage < 50:
        warnings.insert(0, "CRITICAL: Investigation is less than 50% complete. Case closure is NOT recommended.")
    elif not ready:
        warnings.insert(0, "Several investigation steps are incomplete. Review before closing.")

    checklist.append({
        "key": item_def["key"],
        "label": item_def["label"],
        "status": status,
        "details": details,
    })

    return {
        "ready": ready,
        "checklist": checklist,
        "warnings": warnings,
        "completion_percentage": round(completion_percentage, 1),
    }
