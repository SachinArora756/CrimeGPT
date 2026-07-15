"""Investigation Memory Service - persists findings and auto-correlates evidence."""

import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import async_session
from app.models.investigation_memory import InvestigationMemory, EvidenceCorrelation
from app.models.evidence import Evidence

logger = logging.getLogger(__name__)

CORRELATION_THRESHOLDS = {
    "same_face": 0.6,
    "same_vehicle": 0.7,
    "same_plate": 0.95,
    "same_weapon": 0.6,
    "same_object": 0.5,
}


async def store_investigation_findings(
    case_id: int,
    evidence_id: int,
    tool_results: list[dict],
    db: AsyncSession,
) -> list[dict]:
    """Extract key findings from tool results and store in investigation memory."""
    findings_stored = []

    for result in tool_results:
        if result["status"] != "completed" or not result.get("output_data"):
            continue

        output = result["output_data"]
        tool_key = result["tool_key"]
        confidence = result.get("confidence") or 0.0

        extracted = _extract_findings(tool_key, output, confidence)
        for finding in extracted:
            memory_entry = InvestigationMemory(
                case_id=case_id,
                evidence_id=evidence_id,
                finding_type=finding["type"],
                finding_key=finding["key"],
                finding_data=finding["data"],
                embedding_id=finding.get("embedding_id"),
                confidence=finding.get("confidence", confidence),
            )
            db.add(memory_entry)
            findings_stored.append(finding)

    if findings_stored:
        await db.flush()

    return findings_stored


async def correlate_with_case_memory(
    case_id: int,
    evidence_id: int,
    new_findings: list[dict],
    db: AsyncSession,
) -> list[dict]:
    """Compare new findings against all existing case memory to find correlations."""
    correlations = []

    if not new_findings:
        return correlations

    stmt = (
        select(InvestigationMemory)
        .where(InvestigationMemory.case_id == case_id)
        .where(InvestigationMemory.evidence_id != evidence_id)
    )
    result = await db.execute(stmt)
    existing_memories = result.scalars().all()

    if not existing_memories:
        return correlations

    existing_by_type = {}
    for mem in existing_memories:
        existing_by_type.setdefault(mem.finding_type, []).append(mem)

    for finding in new_findings:
        finding_type = finding["type"]
        if finding_type not in existing_by_type:
            continue

        for existing in existing_by_type[finding_type]:
            match_confidence = _calculate_match_confidence(finding, existing)
            correlation_type = f"same_{finding_type}"
            threshold = CORRELATION_THRESHOLDS.get(correlation_type, 0.6)

            if match_confidence >= threshold:
                correlation = EvidenceCorrelation(
                    case_id=case_id,
                    source_evidence_id=evidence_id,
                    target_evidence_id=existing.evidence_id,
                    correlation_type=correlation_type,
                    confidence=match_confidence,
                    details={
                        "source_finding": finding["key"],
                        "target_finding": existing.finding_key,
                        "match_reason": finding.get("data", {}).get("description", ""),
                    },
                )
                db.add(correlation)
                correlations.append({
                    "source_evidence_id": evidence_id,
                    "target_evidence_id": existing.evidence_id,
                    "correlation_type": correlation_type,
                    "confidence": match_confidence,
                    "details": {
                        "source_finding": finding["key"],
                        "target_finding": existing.finding_key,
                    },
                })

    if correlations:
        await db.flush()

    return correlations


async def generate_correlation_report(case_id: int, db: AsyncSession) -> dict:
    """Generate a full cross-evidence correlation report for a case."""
    stmt = (
        select(EvidenceCorrelation)
        .where(EvidenceCorrelation.case_id == case_id)
        .order_by(EvidenceCorrelation.confidence.desc())
    )
    result = await db.execute(stmt)
    all_correlations = result.scalars().all()

    evidence_stmt = select(Evidence).where(Evidence.case_id == case_id)
    ev_result = await db.execute(evidence_stmt)
    evidence_map = {e.id: e.original_filename for e in ev_result.scalars().all()}

    correlations = []
    for corr in all_correlations:
        correlations.append({
            "source_evidence_id": corr.source_evidence_id,
            "target_evidence_id": corr.target_evidence_id,
            "correlation_type": corr.correlation_type,
            "confidence": corr.confidence,
            "source_filename": evidence_map.get(corr.source_evidence_id, "Unknown"),
            "target_filename": evidence_map.get(corr.target_evidence_id, "Unknown"),
            "details": corr.details or {},
        })

    clusters = _build_clusters(all_correlations, evidence_map)

    return {
        "correlations": correlations,
        "clusters": clusters,
        "total_links": len(correlations),
    }


def _extract_findings(tool_key: str, output: dict, confidence: float) -> list[dict]:
    """Extract structured findings from a tool's output."""
    findings = []

    if tool_key == "face_detect":
        faces_count = output.get("faces_detected", 0)
        for i, face in enumerate(output.get("faces", [])[:10]):
            findings.append({
                "type": "face",
                "key": f"face_{i}_{face.get('confidence', 0):.2f}",
                "data": {
                    "description": f"Face detected (age: {face.get('age', 'N/A')}, gender: {face.get('gender', 'N/A')})",
                    "bbox": face.get("bbox"),
                    "age": face.get("age"),
                    "gender": face.get("gender"),
                },
                "confidence": face.get("confidence", confidence),
            })

    elif tool_key == "face_recognize":
        for match in output.get("matches", []):
            findings.append({
                "type": "face",
                "key": f"face_match_{match.get('criminal_id', 'unknown')}",
                "data": {
                    "description": f"Face matched: {match.get('full_name', 'Unknown')}",
                    "criminal_id": match.get("criminal_id"),
                    "similarity": match.get("similarity"),
                },
                "confidence": match.get("similarity", confidence),
            })

    elif tool_key == "vehicle_detect":
        for i, vehicle in enumerate(output.get("vehicles", output.get("detections", []))[:10]):
            label = vehicle.get("label", vehicle.get("class", "vehicle"))
            color = vehicle.get("color", "")
            findings.append({
                "type": "vehicle",
                "key": f"vehicle_{label}_{color}_{i}".lower().replace(" ", "_"),
                "data": {
                    "description": f"{color} {label}".strip(),
                    "color": color,
                    "label": label,
                    "make_model": vehicle.get("make_model", ""),
                },
                "confidence": vehicle.get("confidence", confidence),
            })

    elif tool_key == "license_plate_ocr":
        for plate in output.get("plates", []):
            plate_text = plate.get("text", "").replace(" ", "").upper()
            if plate_text:
                findings.append({
                    "type": "plate",
                    "key": f"plate_{plate_text}",
                    "data": {
                        "description": f"License plate: {plate_text}",
                        "plate_number": plate_text,
                    },
                    "confidence": plate.get("confidence", confidence),
                })

    elif tool_key == "weapon_detect":
        for i, weapon in enumerate(output.get("weapons", output.get("detections", []))[:10]):
            label = weapon.get("label", weapon.get("class", "weapon"))
            findings.append({
                "type": "weapon",
                "key": f"weapon_{label}_{i}".lower().replace(" ", "_"),
                "data": {
                    "description": f"Weapon detected: {label}",
                    "weapon_type": label,
                    "threat_level": weapon.get("threat_level", "unknown"),
                },
                "confidence": weapon.get("confidence", confidence),
            })

    elif tool_key == "image_object_detect":
        for det in output.get("detections", [])[:20]:
            label = det.get("label", det.get("class", "object"))
            findings.append({
                "type": "object",
                "key": f"object_{label}".lower().replace(" ", "_"),
                "data": {
                    "description": label,
                    "bbox": det.get("bbox"),
                },
                "confidence": det.get("confidence", confidence),
            })

    elif tool_key == "fingerprint_match":
        for match in output.get("matches", []):
            findings.append({
                "type": "fingerprint",
                "key": f"fingerprint_match_{match.get('criminal_id', 'unknown')}",
                "data": {
                    "description": f"Fingerprint matched: {match.get('full_name', 'Unknown')}",
                    "criminal_id": match.get("criminal_id"),
                },
                "confidence": match.get("similarity", confidence),
            })

    elif tool_key == "dna_search":
        for match in output.get("matches", []):
            findings.append({
                "type": "dna",
                "key": f"dna_match_{match.get('criminal_id', 'unknown')}",
                "data": {
                    "description": f"DNA matched: {match.get('full_name', 'Unknown')}",
                    "criminal_id": match.get("criminal_id"),
                    "match_percentage": match.get("match_percentage"),
                },
                "confidence": (match.get("match_percentage", 0) / 100.0),
            })

    return findings


def _calculate_match_confidence(finding: dict, existing: InvestigationMemory) -> float:
    """Calculate confidence that two findings refer to the same entity."""
    if finding["type"] == "plate":
        new_plate = finding.get("data", {}).get("plate_number", "")
        existing_plate = (existing.finding_data or {}).get("plate_number", "")
        if new_plate and existing_plate and new_plate == existing_plate:
            return 0.99
        return 0.0

    if finding["type"] == "face":
        if "criminal_id" in finding.get("data", {}) and "criminal_id" in (existing.finding_data or {}):
            if finding["data"]["criminal_id"] == existing.finding_data["criminal_id"]:
                return 0.95
        return 0.0

    if finding["type"] == "vehicle":
        new_data = finding.get("data", {})
        existing_data = existing.finding_data or {}
        score = 0.0
        if new_data.get("color") and existing_data.get("color"):
            if new_data["color"].lower() == existing_data["color"].lower():
                score += 0.4
        if new_data.get("label") and existing_data.get("label"):
            if new_data["label"].lower() == existing_data["label"].lower():
                score += 0.3
        if new_data.get("make_model") and existing_data.get("make_model"):
            if new_data["make_model"].lower() == existing_data["make_model"].lower():
                score += 0.3
        return score

    if finding["type"] == "weapon":
        new_type = finding.get("data", {}).get("weapon_type", "").lower()
        existing_type = (existing.finding_data or {}).get("weapon_type", "").lower()
        if new_type and existing_type and new_type == existing_type:
            return 0.7
        return 0.0

    if finding["type"] in ("fingerprint", "dna"):
        new_cid = finding.get("data", {}).get("criminal_id")
        existing_cid = (existing.finding_data or {}).get("criminal_id")
        if new_cid and existing_cid and new_cid == existing_cid:
            return 0.98
        return 0.0

    return 0.0


def _build_clusters(correlations: list, evidence_map: dict) -> dict:
    """Build entity clusters from correlations."""
    clusters = {}

    for corr in correlations:
        ctype = corr.correlation_type
        if ctype not in clusters:
            clusters[ctype] = []

        source_id = corr.source_evidence_id
        target_id = corr.target_evidence_id

        found_cluster = None
        for cluster in clusters[ctype]:
            if source_id in cluster["evidence_ids"] or target_id in cluster["evidence_ids"]:
                found_cluster = cluster
                break

        if found_cluster:
            found_cluster["evidence_ids"].add(source_id)
            found_cluster["evidence_ids"].add(target_id)
        else:
            clusters[ctype].append({
                "evidence_ids": {source_id, target_id},
                "details": corr.details or {},
            })

    serializable = {}
    for ctype, cluster_list in clusters.items():
        serializable[ctype] = [
            {
                "evidence_ids": list(c["evidence_ids"]),
                "evidence_files": [evidence_map.get(eid, "Unknown") for eid in c["evidence_ids"]],
                "count": len(c["evidence_ids"]),
            }
            for c in cluster_list
        ]

    return serializable
