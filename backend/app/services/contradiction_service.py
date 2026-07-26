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


EVIDENCE_WEIGHT = {
    "dna_search": 0.99,
    "fingerprint_match": 0.95,
    "face_recognize": 0.85,
    "digital_hash": 0.90,
    "license_plate_ocr": 0.80,
    "audio_transcribe": 0.75,
    "vehicle_detect": 0.70,
    "weapon_detect": 0.70,
    "face_detect": 0.65,
    "image_object_detect": 0.60,
    "image_ocr": 0.55,
    "image_exif": 0.50,
    "digital_metadata": 0.45,
}


def build_confidence_dashboard(
    tool_results: list[dict],
    criminal_matches: list[dict],
    contradictions: list[dict],
    hypotheses: list[dict] | None = None,
) -> dict:
    """Build an overall confidence dashboard from all evidence analyses with evidence weighting."""
    scores = {}

    face_results = [r for r in tool_results if r["tool_key"] in ("face_detect", "face_recognize") and r["status"] == "completed"]
    if face_results:
        scores["face_match"] = {
            "confidence": max(r.get("confidence", 0) or 0 for r in face_results),
            "tools_used": len(face_results),
            "evidential_weight": EVIDENCE_WEIGHT.get("face_recognize", 0.85),
            "status": "analyzed",
        }

    fingerprint_results = [r for r in tool_results if r["tool_key"] == "fingerprint_match" and r["status"] == "completed"]
    if fingerprint_results:
        scores["fingerprint"] = {
            "confidence": max(r.get("confidence", 0) or 0 for r in fingerprint_results),
            "tools_used": len(fingerprint_results),
            "evidential_weight": EVIDENCE_WEIGHT.get("fingerprint_match", 0.95),
            "status": "analyzed",
        }

    dna_results = [r for r in tool_results if r["tool_key"] == "dna_search" and r["status"] == "completed"]
    if dna_results:
        scores["dna"] = {
            "confidence": max(r.get("confidence", 0) or 0 for r in dna_results),
            "tools_used": len(dna_results),
            "evidential_weight": EVIDENCE_WEIGHT.get("dna_search", 0.99),
            "status": "analyzed",
        }

    vehicle_results = [r for r in tool_results if r["tool_key"] in ("vehicle_detect", "license_plate_ocr") and r["status"] == "completed"]
    if vehicle_results:
        scores["vehicle"] = {
            "confidence": max(r.get("confidence", 0) or 0 for r in vehicle_results),
            "tools_used": len(vehicle_results),
            "evidential_weight": EVIDENCE_WEIGHT.get("vehicle_detect", 0.70),
            "status": "analyzed",
        }

    ocr_results = [r for r in tool_results if r["tool_key"] in ("image_ocr", "document_ocr", "document_pdf_parse") and r["status"] == "completed"]
    if ocr_results:
        scores["ocr"] = {
            "confidence": max(r.get("confidence", 0) or 0 for r in ocr_results),
            "tools_used": len(ocr_results),
            "evidential_weight": EVIDENCE_WEIGHT.get("image_ocr", 0.55),
            "status": "analyzed",
        }

    weapon_results = [r for r in tool_results if r["tool_key"] == "weapon_detect" and r["status"] == "completed"]
    if weapon_results:
        scores["weapon"] = {
            "confidence": max(r.get("confidence", 0) or 0 for r in weapon_results),
            "tools_used": len(weapon_results),
            "evidential_weight": EVIDENCE_WEIGHT.get("weapon_detect", 0.70),
            "status": "analyzed",
        }

    scene_results = [r for r in tool_results if r["tool_key"] == "crime_scene_analysis" and r["status"] == "completed"]
    if scene_results:
        scores["crime_scene"] = {
            "confidence": max(r.get("confidence", 0) or 0 for r in scene_results),
            "tools_used": len(scene_results),
            "evidential_weight": 0.75,
            "status": "analyzed",
        }

    # Weighted confidence: physical evidence (DNA, fingerprints) counts more than digital
    weighted_sum = 0.0
    weight_total = 0.0
    for s in scores.values():
        conf = s["confidence"]
        w = s.get("evidential_weight", 0.5)
        if conf and conf > 0:
            weighted_sum += conf * w
            weight_total += w

    overall_evidence_confidence = (weighted_sum / weight_total) if weight_total > 0 else 0

    high_severity_count = sum(1 for c in contradictions if c.get("severity") == "high")
    contradiction_penalty = min(high_severity_count * 8 + (len(contradictions) - high_severity_count) * 3, 30)
    overall_investigation_confidence = max(0, overall_evidence_confidence * 100 - contradiction_penalty)

    return {
        "overall_investigation_confidence": round(overall_investigation_confidence, 1),
        "overall_evidence_confidence": round(overall_evidence_confidence * 100, 1),
        "category_scores": scores,
        "contradiction_penalty": contradiction_penalty,
        "contradictions_count": len(contradictions),
        "high_severity_contradictions": high_severity_count,
        "tools_executed": len(tool_results),
        "tools_successful": sum(1 for r in tool_results if r["status"] == "completed"),
        "criminal_matches_found": len(criminal_matches),
        "evidence_weighting": "physical > biometric > digital > metadata",
    }


def _detect_basic_contradictions(tool_results: list[dict]) -> list[dict]:
    """Detect obvious contradictions using rules-based logic."""
    contradictions = []

    # --- Vehicle color conflicts ---
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

    # --- Identity conflicts ---
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

    # --- Temporal conflicts (timestamps that are impossible) ---
    timestamps = []
    for r in tool_results:
        if r["status"] != "completed" or not r.get("output_data"):
            continue
        output = r["output_data"]
        ts = output.get("datetime_original") or output.get("timestamp") or output.get("date_taken")
        if ts:
            try:
                parsed_ts = datetime.fromisoformat(str(ts).replace("Z", "+00:00")) if "T" in str(ts) else datetime.strptime(str(ts)[:19], "%Y:%m:%d %H:%M:%S")
                timestamps.append({"ts": parsed_ts, "tool": r["tool_key"], "source": r.get("execution_id", "")})
            except (ValueError, TypeError):
                pass

    if len(timestamps) >= 2:
        timestamps.sort(key=lambda x: x["ts"])
        first, last = timestamps[0], timestamps[-1]
        delta = (last["ts"] - first["ts"]).total_seconds()
        if delta < 0:
            contradictions.append({
                "id": len(contradictions) + 1,
                "type": "timeline_conflict",
                "severity": "high",
                "description": "Evidence timestamps are in reverse chronological order — possible tampering or clock mismatch",
                "source_a": first["tool"],
                "source_b": last["tool"],
                "finding_a": str(first["ts"]),
                "finding_b": str(last["ts"]),
                "recommendation": "Verify device clocks and chain of custody timestamps",
            })

    # --- Location conflicts (EXIF GPS from different evidence items) ---
    gps_locations = []
    for r in tool_results:
        if r["status"] != "completed" or not r.get("output_data"):
            continue
        output = r["output_data"]
        lat = output.get("gps_latitude") or output.get("latitude")
        lon = output.get("gps_longitude") or output.get("longitude")
        if lat and lon:
            try:
                gps_locations.append({
                    "lat": float(lat), "lon": float(lon),
                    "tool": r["tool_key"], "source": r.get("execution_id", ""),
                })
            except (ValueError, TypeError):
                pass

    if len(gps_locations) >= 2:
        from math import radians, sin, cos, sqrt, atan2
        for i in range(len(gps_locations)):
            for j in range(i + 1, len(gps_locations)):
                a, b = gps_locations[i], gps_locations[j]
                R = 6371000
                lat1, lat2 = radians(a["lat"]), radians(b["lat"])
                dlat = lat2 - lat1
                dlon = radians(b["lon"] - a["lon"])
                h = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
                distance_m = R * 2 * atan2(sqrt(h), sqrt(1 - h))
                if distance_m > 5000:
                    contradictions.append({
                        "id": len(contradictions) + 1,
                        "type": "location_conflict",
                        "severity": "high" if distance_m > 50000 else "medium",
                        "description": f"Evidence items are {distance_m / 1000:.1f} km apart — verify if same incident",
                        "source_a": a["tool"],
                        "source_b": b["tool"],
                        "finding_a": f"GPS: {a['lat']:.5f}, {a['lon']:.5f}",
                        "finding_b": f"GPS: {b['lat']:.5f}, {b['lon']:.5f}",
                        "recommendation": "Confirm whether evidence items belong to the same crime scene or incident",
                    })
                    break
            else:
                continue
            break

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
