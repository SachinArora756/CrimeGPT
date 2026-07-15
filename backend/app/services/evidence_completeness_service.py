"""Evidence Completeness Engine - ensures no evidence is left unanalyzed."""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.forensic_toolkit import ForensicToolExecution, ExecutionStatus
from app.models.evidence import Evidence
from app.services.ai_investigation_service import CLASSIFICATION_TOOL_MAP

logger = logging.getLogger(__name__)

TOOL_DISPLAY_NAMES = {
    "digital_hash": "Digital Hash",
    "digital_metadata": "Digital Metadata",
    "digital_file_identify": "File Identification",
    "image_exif": "EXIF Metadata",
    "face_detect": "Face Detection",
    "face_recognize": "Face Recognition",
    "fingerprint_match": "Fingerprint Matching",
    "dna_search": "DNA Search",
    "vehicle_detect": "Vehicle Detection",
    "license_plate_ocr": "License Plate OCR",
    "weapon_detect": "Weapon Detection",
    "image_object_detect": "Object Detection",
    "image_ocr": "Image OCR",
    "image_similarity": "Image Similarity",
    "document_ocr": "Document OCR",
    "document_pdf_parse": "PDF Parsing",
    "document_summarize": "Document Summary",
    "crime_scene_analysis": "Crime Scene Analysis",
    "audio_transcribe": "Audio Transcription",
}

CHECKLIST_CATEGORIES = [
    {"category": "Faces", "tools": ["face_detect", "face_recognize"], "finding_keys": ["faces_detected", "matches_found"]},
    {"category": "Vehicles", "tools": ["vehicle_detect"], "finding_keys": ["vehicles_detected"]},
    {"category": "Weapons", "tools": ["weapon_detect"], "finding_keys": ["weapons_detected"]},
    {"category": "Mobile Phones", "tools": ["image_object_detect"], "finding_keys": ["cell phone"]},
    {"category": "IDs/Documents", "tools": ["image_ocr", "document_ocr"], "finding_keys": ["text_found"]},
    {"category": "Fingerprints", "tools": ["fingerprint_match"], "finding_keys": ["matches_found"]},
    {"category": "Shoe Prints", "tools": ["image_object_detect", "crime_scene_analysis"], "finding_keys": ["shoe", "footwear"]},
    {"category": "Blood-like Regions", "tools": ["crime_scene_analysis"], "finding_keys": ["blood", "stain"]},
    {"category": "Glass Fragments", "tools": ["image_object_detect", "crime_scene_analysis"], "finding_keys": ["glass"]},
    {"category": "Tire Marks", "tools": ["image_object_detect", "crime_scene_analysis"], "finding_keys": ["tire"]},
    {"category": "Currency", "tools": ["image_object_detect", "image_ocr"], "finding_keys": ["currency", "money", "cash"]},
    {"category": "License Plates", "tools": ["license_plate_ocr"], "finding_keys": ["plates_detected"]},
    {"category": "Metadata", "tools": ["image_exif", "digital_metadata"], "finding_keys": ["metadata"]},
]


def generate_checklist(tool_results: list[dict], evidence_type: str) -> dict:
    """Generate evidence analysis checklist from tool results."""
    items = []

    for cat_def in CHECKLIST_CATEGORIES:
        category = cat_def["category"]
        relevant_tools = cat_def["tools"]
        finding_keys = cat_def["finding_keys"]

        matching_results = [r for r in tool_results if r["tool_key"] in relevant_tools]

        if not matching_results:
            applicable = _is_category_applicable(category, evidence_type)
            items.append({
                "category": category,
                "state": "not_applicable" if not applicable else "not_found",
                "findings_count": 0,
                "confidence": 0.0,
                "details": "" if not applicable else "Analysis not performed",
            })
            continue

        completed_results = [r for r in matching_results if r["status"] == "completed"]
        if not completed_results:
            items.append({
                "category": category,
                "state": "needs_manual_review",
                "findings_count": 0,
                "confidence": 0.0,
                "details": "Tool execution failed",
            })
            continue

        findings_count = 0
        max_confidence = 0.0
        for r in completed_results:
            output = r.get("output_data") or {}
            conf = r.get("confidence") or 0.0
            max_confidence = max(max_confidence, conf)

            for key in finding_keys:
                if key in output:
                    val = output[key]
                    if isinstance(val, int):
                        findings_count += val
                    elif isinstance(val, bool) and val:
                        findings_count += 1
                    elif isinstance(val, list):
                        findings_count += len(val)
                    elif isinstance(val, str) and val:
                        findings_count += 1

            if findings_count == 0:
                output_str = str(output).lower()
                for key in finding_keys:
                    if key in output_str:
                        findings_count += 1
                        break

        if findings_count > 0:
            state = "completed"
            details = f"Found {findings_count} item(s)"
        elif max_confidence > 0:
            state = "not_found"
            details = "Analysis ran but nothing detected"
        else:
            state = "needs_manual_review"
            details = "Low confidence results"

        items.append({
            "category": category,
            "state": state,
            "findings_count": findings_count,
            "confidence": max_confidence,
            "details": details,
        })

    completed_count = sum(1 for i in items if i["state"] == "completed")
    not_found_count = sum(1 for i in items if i["state"] == "not_found")
    needs_review_count = sum(1 for i in items if i["state"] == "needs_manual_review")

    return {
        "items": items,
        "total_categories": len(items),
        "completed_count": completed_count,
        "not_found_count": not_found_count,
        "needs_review_count": needs_review_count,
    }


def calculate_completeness(
    tool_results: list[dict],
    evidence_type: str,
    checklist: dict,
    has_correlations: bool = False,
) -> dict:
    """Calculate evidence analysis completeness scores."""
    expected_tools = CLASSIFICATION_TOOL_MAP.get(evidence_type, CLASSIFICATION_TOOL_MAP["unknown"])
    executed_tools = [r["tool_key"] for r in tool_results]
    successful_tools = [r["tool_key"] for r in tool_results if r["status"] == "completed"]

    collection_score = len(executed_tools) / max(len(expected_tools), 1) * 100
    collection_score = min(collection_score, 100.0)

    analysis_score = len(successful_tools) / max(len(executed_tools), 1) * 100 if executed_tools else 0

    applicable_items = [i for i in checklist["items"] if i["state"] != "not_applicable"]
    verified_items = [i for i in applicable_items if i["state"] == "completed"]
    verification_score = len(verified_items) / max(len(applicable_items), 1) * 100 if applicable_items else 100.0

    if has_correlations:
        verification_score = min(verification_score + 10, 100.0)

    overall = (collection_score * 0.3 + analysis_score * 0.4 + verification_score * 0.3)

    missing = []
    for tool in expected_tools:
        if tool not in executed_tools:
            display = TOOL_DISPLAY_NAMES.get(tool, tool)
            missing.append(f"Run {display} on this evidence")

    for item in checklist["items"]:
        if item["state"] == "needs_manual_review":
            missing.append(f"Manual review needed for: {item['category']}")

    recommendations = []
    if analysis_score < 80:
        recommendations.append("Re-run failed analyses for better coverage")
    if verification_score < 50:
        recommendations.append("Cross-reference findings with criminal database")
    if not has_correlations:
        recommendations.append("Upload additional evidence to enable cross-correlation")
    if "face_detect" not in executed_tools and evidence_type in ("crime_scene", "generic_image"):
        recommendations.append("Consider running face detection for suspect identification")
    if "weapon_detect" not in executed_tools and evidence_type == "crime_scene":
        recommendations.append("Run weapon detection on crime scene imagery")

    return {
        "scores": {
            "evidence_collection_score": round(collection_score, 1),
            "evidence_analysis_score": round(analysis_score, 1),
            "evidence_verification_score": round(verification_score, 1),
            "overall_completeness": round(overall, 1),
        },
        "missing_analyses": missing,
        "recommendations": recommendations,
    }


def _is_category_applicable(category: str, evidence_type: str) -> bool:
    """Determine if a checklist category is applicable for the evidence type."""
    non_image_types = ("audio", "document_pdf", "dna_report")
    image_only_categories = (
        "Faces", "Vehicles", "Weapons", "Mobile Phones",
        "Shoe Prints", "Blood-like Regions", "Glass Fragments",
        "Tire Marks", "License Plates",
    )
    if evidence_type in non_image_types and category in image_only_categories:
        return False
    if evidence_type == "fingerprint" and category not in ("Fingerprints", "Metadata"):
        return False
    return True


async def get_case_completeness_stats(case_id: int, db: AsyncSession) -> dict:
    """Get aggregated completeness stats for all evidence in a case."""
    stmt = (
        select(
            func.count(ForensicToolExecution.id).label("total_executions"),
            func.count(ForensicToolExecution.id).filter(
                ForensicToolExecution.status == ExecutionStatus.COMPLETED
            ).label("successful"),
            func.count(ForensicToolExecution.id).filter(
                ForensicToolExecution.status == ExecutionStatus.FAILED
            ).label("failed"),
            func.avg(ForensicToolExecution.confidence_score).label("avg_confidence"),
        )
        .where(ForensicToolExecution.case_id == case_id)
    )
    result = await db.execute(stmt)
    row = result.one_or_none()

    if not row or row.total_executions == 0:
        return {
            "total_executions": 0,
            "successful": 0,
            "failed": 0,
            "avg_confidence": 0.0,
            "success_rate": 0.0,
        }

    return {
        "total_executions": row.total_executions,
        "successful": row.successful,
        "failed": row.failed,
        "avg_confidence": round(float(row.avg_confidence or 0), 2),
        "success_rate": round(row.successful / row.total_executions * 100, 1),
    }
