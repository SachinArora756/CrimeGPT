"""Contradiction Detection Service — identifies conflicting evidence and builds confidence scores."""

import json
import asyncio
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.forensic_toolkit import ForensicToolExecution, ExecutionStatus

logger = logging.getLogger(__name__)

CONTRADICTION_PROMPT = """You are a forensic evidence analyst. Identify contradictions between evidence items.

EVIDENCE ANALYSIS RESULTS:
{evidence_data}

Look for:
1. Color discrepancies (witness says blue vehicle, AI detects white vehicle)
2. Object conflicts (weapon type mismatch between evidence items)
3. Location inconsistencies (EXIF GPS vs reported scene location)
4. Timeline conflicts (timestamps that don't align)
5. Identity conflicts (different suspects identified in same evidence)

Respond with ONLY a JSON object:
{{
  "contradictions": [
    {{
      "id": 1,
      "type": "color_mismatch|identity_conflict|timeline_conflict|location_conflict|object_conflict|other",
      "severity": "high|medium|low",
      "description": "what contradicts what",
      "source_a": "first evidence source",
      "source_b": "second evidence source",
      "finding_a": "what source A says",
      "finding_b": "what source B says",
      "recommendation": "how to resolve"
    }}
  ]
}}

If no contradictions found, return {{"contradictions": []}}
ONLY report genuine contradictions found in the data. Do NOT fabricate contradictions."""


async def detect_contradictions(
    tool_results: list[dict],
    criminal_matches: list[dict] | None = None,
) -> dict:
    """Detect contradictions across evidence analysis results."""
    basic_contradictions = _detect_basic_contradictions(tool_results)

    ai_contradictions = await _detect_ai_contradictions(tool_results)

    all_contradictions = basic_contradictions + ai_contradictions

    seen = set()
    unique = []
    for c in all_contradictions:
        key = (c.get("source_a", ""), c.get("source_b", ""), c.get("type", ""))
        if key not in seen:
            seen.add(key)
            unique.append(c)

    unique.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x.get("severity", "low"), 3))

    return {
        "contradictions": unique,
        "total_contradictions": len(unique),
        "high_severity": sum(1 for c in unique if c.get("severity") == "high"),
        "has_contradictions": len(unique) > 0,
    }


def build_confidence_dashboard(
    tool_results: list[dict],
    criminal_matches: list[dict],
    contradictions: list[dict],
    hypotheses: list[dict] | None = None,
) -> dict:
    """Build an overall confidence dashboard from all evidence analyses."""
    scores = {}

    face_results = [r for r in tool_results if r["tool_key"] in ("face_detect", "face_recognize") and r["status"] == "completed"]
    if face_results:
        scores["face_match"] = {
            "confidence": max(r.get("confidence", 0) or 0 for r in face_results),
            "tools_used": len(face_results),
            "status": "analyzed",
        }

    fingerprint_results = [r for r in tool_results if r["tool_key"] == "fingerprint_match" and r["status"] == "completed"]
    if fingerprint_results:
        scores["fingerprint"] = {
            "confidence": max(r.get("confidence", 0) or 0 for r in fingerprint_results),
            "tools_used": len(fingerprint_results),
            "status": "analyzed",
        }

    dna_results = [r for r in tool_results if r["tool_key"] == "dna_search" and r["status"] == "completed"]
    if dna_results:
        scores["dna"] = {
            "confidence": max(r.get("confidence", 0) or 0 for r in dna_results),
            "tools_used": len(dna_results),
            "status": "analyzed",
        }

    vehicle_results = [r for r in tool_results if r["tool_key"] in ("vehicle_detect", "license_plate_ocr") and r["status"] == "completed"]
    if vehicle_results:
        scores["vehicle"] = {
            "confidence": max(r.get("confidence", 0) or 0 for r in vehicle_results),
            "tools_used": len(vehicle_results),
            "status": "analyzed",
        }

    ocr_results = [r for r in tool_results if r["tool_key"] in ("image_ocr", "document_ocr", "document_pdf_parse") and r["status"] == "completed"]
    if ocr_results:
        scores["ocr"] = {
            "confidence": max(r.get("confidence", 0) or 0 for r in ocr_results),
            "tools_used": len(ocr_results),
            "status": "analyzed",
        }

    weapon_results = [r for r in tool_results if r["tool_key"] == "weapon_detect" and r["status"] == "completed"]
    if weapon_results:
        scores["weapon"] = {
            "confidence": max(r.get("confidence", 0) or 0 for r in weapon_results),
            "tools_used": len(weapon_results),
            "status": "analyzed",
        }

    scene_results = [r for r in tool_results if r["tool_key"] == "crime_scene_analysis" and r["status"] == "completed"]
    if scene_results:
        scores["crime_scene"] = {
            "confidence": max(r.get("confidence", 0) or 0 for r in scene_results),
            "tools_used": len(scene_results),
            "status": "analyzed",
        }

    all_confidences = [s["confidence"] for s in scores.values() if s["confidence"] and s["confidence"] > 0]
    overall_evidence_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0

    contradiction_penalty = min(len(contradictions) * 5, 20)
    overall_investigation_confidence = max(0, overall_evidence_confidence * 100 - contradiction_penalty)

    return {
        "overall_investigation_confidence": round(overall_investigation_confidence, 1),
        "overall_evidence_confidence": round(overall_evidence_confidence * 100, 1),
        "category_scores": scores,
        "contradiction_penalty": contradiction_penalty,
        "contradictions_count": len(contradictions),
        "tools_executed": len(tool_results),
        "tools_successful": sum(1 for r in tool_results if r["status"] == "completed"),
        "criminal_matches_found": len(criminal_matches),
    }


def _detect_basic_contradictions(tool_results: list[dict]) -> list[dict]:
    """Detect obvious contradictions using rules-based logic."""
    contradictions = []

    vehicle_detections = []
    for r in tool_results:
        if r["tool_key"] == "vehicle_detect" and r["status"] == "completed" and r.get("output_data"):
            output = r["output_data"]
            for v in output.get("vehicles", output.get("detections", [])):
                vehicle_detections.append({
                    "color": v.get("color", ""),
                    "type": v.get("label", v.get("class", "")),
                    "source": r.get("execution_id", "unknown"),
                })

    colors_found = set(v["color"].lower() for v in vehicle_detections if v["color"])
    if len(colors_found) > 1:
        contradictions.append({
            "id": len(contradictions) + 1,
            "type": "color_mismatch",
            "severity": "medium",
            "description": f"Multiple vehicle colors detected: {', '.join(colors_found)}",
            "source_a": "Vehicle Detection (evidence 1)",
            "source_b": "Vehicle Detection (evidence 2)",
            "finding_a": list(colors_found)[0] if colors_found else "",
            "finding_b": list(colors_found)[1] if len(colors_found) > 1 else "",
            "recommendation": "Verify if multiple vehicles are present or if detection is inconsistent",
        })

    face_ids = []
    for r in tool_results:
        if r["tool_key"] == "face_recognize" and r["status"] == "completed" and r.get("output_data"):
            for match in r["output_data"].get("matches", []):
                face_ids.append(match.get("criminal_id"))

    if len(set(face_ids)) > 1:
        contradictions.append({
            "id": len(contradictions) + 1,
            "type": "identity_conflict",
            "severity": "high",
            "description": f"Multiple different suspects identified across evidence ({len(set(face_ids))} unique IDs)",
            "source_a": "Face Recognition",
            "source_b": "Face Recognition",
            "finding_a": f"Suspect ID: {face_ids[0]}",
            "finding_b": f"Suspect ID: {face_ids[1] if len(face_ids) > 1 else 'N/A'}",
            "recommendation": "Review all face recognition results — multiple suspects or misidentification possible",
        })

    return contradictions


async def _detect_ai_contradictions(tool_results: list[dict]) -> list[dict]:
    """Use LLM to detect subtle contradictions across evidence."""
    try:
        from app.ai.llm_provider import has_any_llm_key, generate_text

        if not has_any_llm_key():
            return []

        completed_results = [r for r in tool_results if r["status"] == "completed" and r.get("output_data")]
        if len(completed_results) < 2:
            return []

        evidence_lines = []
        for r in completed_results[:10]:
            output_str = json.dumps(r["output_data"], default=str)[:1000]
            evidence_lines.append(f"[{r['tool_key']}]: {output_str}")

        prompt = CONTRADICTION_PROMPT.format(evidence_data="\n".join(evidence_lines))
        response = await asyncio.to_thread(generate_text, prompt, 0.2, 1500)
        parsed = json.loads(response.strip().strip("```json").strip("```").strip())

        return parsed.get("contradictions", [])

    except Exception as e:
        logger.warning(f"AI contradiction detection failed: {e}")
        return []
