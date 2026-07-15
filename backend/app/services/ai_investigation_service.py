"""
AI Investigation Copilot Service — Intelligent Evidence Assurance Engine (IEAE)

Orchestrates: Evidence Classification (AI-enhanced) → Intelligent Tool Planning →
Multi-Pass Parallel Execution → Evidence Checklist → Completeness Scoring →
Investigation Memory → Cross-Evidence Correlation → Criminal Intelligence →
LLM Report Generation (fact-only)
"""

import os
import uuid
import json
import time
import asyncio
import logging
import mimetypes
from datetime import datetime
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import async_session
from app.models.forensic_toolkit import ForensicToolExecution, ExecutionStatus
from app.models.criminal_intelligence import (
    CriminalProfile, CriminalVehicle, CriminalFaceEmbedding,
)
from app.services.forensic_tools_service import TOOL_HANDLERS

logger = logging.getLogger(__name__)

EVIDENCE_DIR = "data/ai-investigation"

CLASSIFICATION_TOOL_MAP = {
    "face": ["digital_hash", "face_detect", "face_recognize", "image_exif"],
    "vehicle": ["digital_hash", "vehicle_detect", "license_plate_ocr", "image_exif"],
    "fingerprint": ["digital_hash", "fingerprint_match"],
    "crime_scene": ["digital_hash", "image_object_detect", "weapon_detect", "vehicle_detect", "license_plate_ocr", "face_detect", "image_exif"],
    "document_pdf": ["digital_hash", "document_pdf_parse", "document_summarize"],
    "document_image": ["digital_hash", "image_ocr", "document_summarize"],
    "audio": ["digital_hash", "audio_transcribe"],
    "dna_report": ["digital_hash", "dna_search"],
    "generic_image": ["digital_hash", "image_ocr", "image_object_detect", "image_exif", "digital_metadata"],
    "unknown": ["digital_hash", "digital_metadata", "digital_file_identify"],
}

TOOL_DISPLAY_NAMES = {
    "digital_hash": "Digital Hash Verification",
    "digital_metadata": "Digital Metadata Extraction",
    "digital_file_identify": "File Type Identification",
    "image_exif": "EXIF/GPS Metadata",
    "face_detect": "Face Detection",
    "face_recognize": "Face Recognition",
    "fingerprint_match": "Fingerprint Matching",
    "dna_search": "DNA Database Search",
    "vehicle_detect": "Vehicle Detection",
    "license_plate_ocr": "License Plate OCR",
    "weapon_detect": "Weapon Detection",
    "image_object_detect": "Object Detection",
    "image_ocr": "Image OCR",
    "image_similarity": "Image Similarity Search",
    "document_ocr": "Document OCR",
    "document_pdf_parse": "PDF Parsing",
    "document_summarize": "Document Summarization",
    "crime_scene_analysis": "Crime Scene Analysis",
    "audio_transcribe": "Audio Transcription",
}


def _summarize_findings(result: dict) -> str:
    """Generate a one-line summary of tool findings for pass reporting."""
    if result["status"] != "completed" or not result.get("output_data"):
        return f"Failed: {result.get('error', 'Unknown error')[:80]}" if result["status"] == "failed" else "No data"

    output = result["output_data"]
    tool_key = result["tool_key"]

    if tool_key == "face_detect":
        count = output.get("faces_detected", 0)
        return f"{count} face(s) detected" if count else "No faces detected"
    elif tool_key == "face_recognize":
        count = output.get("matches_found", 0)
        return f"{count} criminal match(es)" if count else "No matches in database"
    elif tool_key == "vehicle_detect":
        count = output.get("vehicles_detected", len(output.get("detections", [])))
        return f"{count} vehicle(s) detected" if count else "No vehicles detected"
    elif tool_key == "license_plate_ocr":
        count = output.get("plates_detected", 0)
        plates = [p.get("text", "") for p in output.get("plates", [])[:3]]
        return f"{count} plate(s): {', '.join(plates)}" if count else "No plates detected"
    elif tool_key == "weapon_detect":
        count = output.get("weapons_detected", len(output.get("detections", [])))
        return f"{count} weapon(s) detected" if count else "No weapons detected"
    elif tool_key == "image_object_detect":
        detections = output.get("detections", [])
        labels = list(set(d.get("label", d.get("class", "")) for d in detections[:10]))
        return f"{len(detections)} objects: {', '.join(labels[:5])}" if detections else "No objects detected"
    elif tool_key in ("image_ocr", "document_ocr"):
        text = output.get("text", "")
        return f"Text extracted ({len(text)} chars)" if text else "No text found"
    elif tool_key == "digital_hash":
        sha = output.get("sha256", "")[:16]
        return f"SHA-256: {sha}..." if sha else "Hash computed"
    elif tool_key == "fingerprint_match":
        count = output.get("matches_found", 0)
        return f"{count} fingerprint match(es)" if count else "No matches"
    elif tool_key == "dna_search":
        count = output.get("matches_found", 0)
        return f"{count} DNA match(es)" if count else "No matches"
    elif tool_key == "image_exif":
        has_gps = bool(output.get("gps"))
        return f"Metadata extracted (GPS: {'Yes' if has_gps else 'No'})"
    elif tool_key == "audio_transcribe":
        text = output.get("transcription", output.get("text", ""))
        return f"Transcribed ({len(text)} chars)" if text else "No speech detected"

    return "Analysis complete"


def classify_evidence(file_path: str, original_filename: str) -> dict:
    """Classify evidence type based on file extension, MIME type, and filename hints."""
    ext = os.path.splitext(original_filename)[1].lower()
    mime_type, _ = mimetypes.guess_type(original_filename)
    mime_type = mime_type or "application/octet-stream"
    name_lower = original_filename.lower()

    if ext == ".pdf" or mime_type == "application/pdf":
        if any(kw in name_lower for kw in ["dna", "str", "loci", "genetic"]):
            return {"type": "dna_report", "mime_type": mime_type, "confidence": 0.8}
        return {"type": "document_pdf", "mime_type": mime_type, "confidence": 0.9}

    if mime_type.startswith("audio/") or ext in (".wav", ".mp3", ".ogg", ".flac", ".m4a"):
        return {"type": "audio", "mime_type": mime_type, "confidence": 0.95}

    if mime_type.startswith("image/") or ext in (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"):
        if any(kw in name_lower for kw in ["fingerprint", "print", "thumb", "latent"]):
            return {"type": "fingerprint", "mime_type": mime_type, "confidence": 0.85}
        if any(kw in name_lower for kw in ["face", "mugshot", "portrait", "selfie", "suspect"]):
            return {"type": "face", "mime_type": mime_type, "confidence": 0.85}
        if any(kw in name_lower for kw in ["vehicle", "car", "plate", "license", "number_plate"]):
            return {"type": "vehicle", "mime_type": mime_type, "confidence": 0.85}
        if any(kw in name_lower for kw in ["crime_scene", "scene", "location", "spot"]):
            return {"type": "crime_scene", "mime_type": mime_type, "confidence": 0.8}
        if any(kw in name_lower for kw in ["document", "letter", "notice", "form", "scan"]):
            return {"type": "document_image", "mime_type": mime_type, "confidence": 0.8}
        return {"type": "generic_image", "mime_type": mime_type, "confidence": 0.5}

    if ext in (".txt", ".csv") or mime_type.startswith("text/"):
        if any(kw in name_lower for kw in ["dna", "str", "loci", "genetic"]):
            return {"type": "dna_report", "mime_type": mime_type, "confidence": 0.8}
        return {"type": "document_image", "mime_type": mime_type, "confidence": 0.6}

    return {"type": "unknown", "mime_type": mime_type, "confidence": 0.3}


# --- IEAE Feature 1: AI-Powered Evidence Classification ---

AI_CLASSIFICATION_PROMPT = """You are a forensic evidence classifier. Analyze this image and classify it into EXACTLY ONE of these categories:

- face: Image primarily showing a person's face, mugshot, or portrait
- vehicle: Image primarily showing a vehicle, car, truck, motorcycle
- weapon: Image showing weapons (knife, gun, rod, etc.)
- crime_scene: Wide-angle shot of a crime scene, location with evidence markers
- fingerprint: Image of fingerprint or palm print
- document_image: Scanned document, letter, ID card, form
- generic_image: General image that doesn't fit above categories

Respond with ONLY a JSON object:
{"type": "<category>", "confidence": <0.0-1.0>, "description": "<brief description of what you see>", "detected_elements": ["<element1>", "<element2>"]}

Be precise. If you see multiple elements (e.g., a person AND a vehicle), classify by the PRIMARY subject."""


async def classify_evidence_with_ai(file_path: str, basic_classification: dict) -> dict:
    """Use Gemini Vision for content-based classification when rules are uncertain."""
    if basic_classification["confidence"] >= 0.8:
        return basic_classification

    mime_type = basic_classification.get("mime_type", "")
    if not mime_type.startswith("image/"):
        return basic_classification

    try:
        from app.ai.llm_provider import has_any_llm_key, generate_vision

        if not has_any_llm_key():
            return basic_classification

        response = await asyncio.to_thread(
            generate_vision, file_path, AI_CLASSIFICATION_PROMPT, 0.1, 500
        )

        parsed = json.loads(response.strip().strip("```json").strip("```").strip())
        ai_type = parsed.get("type", "").lower()
        ai_confidence = float(parsed.get("confidence", 0.5))
        detected_elements = parsed.get("detected_elements", [])

        valid_types = set(CLASSIFICATION_TOOL_MAP.keys())
        if ai_type not in valid_types:
            ai_type = basic_classification["type"]

        if ai_confidence > basic_classification["confidence"]:
            return {
                "type": ai_type,
                "mime_type": basic_classification["mime_type"],
                "confidence": ai_confidence,
                "ai_enhanced": True,
                "description": parsed.get("description", ""),
                "detected_elements": detected_elements,
            }

        return basic_classification

    except Exception as e:
        logger.warning(f"AI classification failed, using rules-based: {e}")
        return basic_classification


# --- IEAE Feature 2: AI Planner Agent ---

AI_PLANNER_PROMPT = """You are a forensic investigation planner. Based on the evidence classification and detected elements, determine which additional forensic tools should be executed.

Evidence Classification: {classification_type}
Confidence: {confidence}
Detected Elements: {detected_elements}
Description: {description}

Available tools (only select from this list):
{available_tools}

Base tools already planned: {base_tools}

Rules:
1. ALWAYS keep base tools (especially digital_hash)
2. ADD tools if detected elements warrant them (e.g., if a face is visible in a vehicle image, add face_detect)
3. Do NOT add tools that are irrelevant (e.g., no audio_transcribe for images)
4. Prioritize: safety tools first, then identification, then context

Respond with ONLY a JSON object:
{{"additional_tools": ["tool_key1", "tool_key2"], "reasoning": "brief explanation"}}"""


async def plan_tools_with_ai(classification: dict, base_plan: dict) -> dict:
    """Use AI to intelligently extend the tool plan based on content analysis."""
    detected_elements = classification.get("detected_elements", [])
    if not detected_elements and not classification.get("ai_enhanced"):
        return base_plan

    try:
        from app.ai.llm_provider import has_any_llm_key, generate_text

        if not has_any_llm_key():
            return base_plan

        available_tools = list(TOOL_HANDLERS.keys())
        prompt = AI_PLANNER_PROMPT.format(
            classification_type=classification["type"],
            confidence=classification["confidence"],
            detected_elements=", ".join(detected_elements) if detected_elements else "None detected",
            description=classification.get("description", "N/A"),
            available_tools=", ".join(available_tools),
            base_tools=", ".join(base_plan["tools_selected"]),
        )

        response = await asyncio.to_thread(generate_text, prompt, 0.1, 300)
        parsed = json.loads(response.strip().strip("```json").strip("```").strip())
        additional_tools = parsed.get("additional_tools", [])
        reasoning = parsed.get("reasoning", "")

        valid_additions = [t for t in additional_tools if t in available_tools and t not in base_plan["tools_selected"]]

        if valid_additions:
            enhanced_tools = base_plan["tools_selected"] + valid_additions
            metadata_tools = ("digital_hash", "digital_metadata", "digital_file_identify", "image_exif")
            parallel_group_1 = [t for t in enhanced_tools if t in metadata_tools]
            parallel_group_2 = [t for t in enhanced_tools if t not in metadata_tools]

            return {
                "tools_selected": enhanced_tools,
                "tools_skipped": base_plan["tools_skipped"],
                "parallel_groups": [parallel_group_1, parallel_group_2] if parallel_group_1 else [parallel_group_2],
                "evidence_type": base_plan["evidence_type"],
                "ai_enhanced": True,
                "ai_reasoning": reasoning,
                "additional_tools": valid_additions,
            }

        return base_plan

    except Exception as e:
        logger.warning(f"AI planner failed, using static plan: {e}")
        return base_plan


def get_tools_for_classification(classification: dict) -> dict:
    """Get tool plan based on evidence classification."""
    evidence_type = classification["type"]
    tools = CLASSIFICATION_TOOL_MAP.get(evidence_type, CLASSIFICATION_TOOL_MAP["unknown"])

    available_tools = list(TOOL_HANDLERS.keys())
    valid_tools = [t for t in tools if t in available_tools]

    all_possible = set(available_tools)
    selected_set = set(valid_tools)
    skipped = []
    for tool in all_possible - selected_set:
        skipped.append({"tool": tool, "reason": f"Not relevant for {evidence_type} evidence"})

    parallel_group_1 = [t for t in valid_tools if t in ("digital_hash", "digital_metadata", "digital_file_identify", "image_exif")]
    parallel_group_2 = [t for t in valid_tools if t not in parallel_group_1]

    return {
        "tools_selected": valid_tools,
        "tools_skipped": skipped,
        "parallel_groups": [parallel_group_1, parallel_group_2] if parallel_group_1 else [parallel_group_2],
        "evidence_type": evidence_type,
    }


async def execute_single_tool(
    tool_key: str,
    file_path: str,
    user_id: int,
    case_id: int | None,
    db: AsyncSession | None = None,
) -> dict:
    """Execute a single forensic tool and record the result.

    Uses its own DB session for safe parallel execution via asyncio.gather.
    """
    execution_id = str(uuid.uuid4())
    filename = os.path.basename(file_path)

    async with async_session() as own_db:
        execution = ForensicToolExecution(
            execution_id=execution_id,
            tool_key=tool_key,
            user_id=user_id,
            case_id=case_id,
            status=ExecutionStatus.PENDING,
            input_filename=filename,
            input_file_path=file_path,
            input_metadata={"source": "ai_investigation"},
        )
        own_db.add(execution)
        await own_db.flush()

        execution.status = ExecutionStatus.RUNNING
        await own_db.flush()

        start_time = time.time()
        try:
            handler = TOOL_HANDLERS[tool_key]
            output_data, confidence = await handler(file_path, {})
            elapsed_ms = int((time.time() - start_time) * 1000)

            execution.output_data = output_data
            execution.confidence_score = confidence
            execution.execution_time_ms = elapsed_ms
            execution.completed_at = datetime.utcnow()

            if output_data.get("error"):
                execution.status = ExecutionStatus.FAILED
                execution.error_message = output_data["error"]
            else:
                execution.status = ExecutionStatus.COMPLETED

            await own_db.commit()

            return {
                "tool_key": tool_key,
                "execution_id": execution_id,
                "status": execution.status.value,
                "confidence": confidence,
                "execution_time_ms": elapsed_ms,
                "output_data": output_data,
                "error": output_data.get("error"),
            }
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)[:500]
            execution.execution_time_ms = elapsed_ms
            execution.completed_at = datetime.utcnow()
            await own_db.commit()

            return {
                "tool_key": tool_key,
                "execution_id": execution_id,
                "status": "failed",
                "confidence": None,
                "execution_time_ms": elapsed_ms,
                "output_data": None,
                "error": str(e)[:200],
            }


async def execute_tool_groups(
    plan: dict,
    file_path: str,
    user_id: int,
    case_id: int | None,
    db: AsyncSession | None = None,
) -> list[dict]:
    """Execute tool groups — tools within a group run in parallel."""
    all_results = []

    for group in plan["parallel_groups"]:
        if not group:
            continue
        tasks = [
            execute_single_tool(tool_key, file_path, user_id, case_id)
            for tool_key in group
        ]
        group_results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(group_results):
            if isinstance(result, Exception):
                all_results.append({
                    "tool_key": group[i],
                    "execution_id": None,
                    "status": "failed",
                    "confidence": None,
                    "execution_time_ms": 0,
                    "output_data": None,
                    "error": str(result)[:200],
                })
            else:
                all_results.append(result)

    return all_results


async def search_criminal_intelligence(
    tool_results: list[dict], db: AsyncSession
) -> list[dict]:
    """Search criminal DB based on tool results."""
    criminal_matches = []

    for result in tool_results:
        if result["status"] != "completed" or not result.get("output_data"):
            continue
        output = result["output_data"]
        tool_key = result["tool_key"]

        if tool_key == "face_recognize" and output.get("matches_found", 0) > 0:
            for match in output.get("matches", []):
                criminal_matches.append({
                    "match_type": "face_recognition",
                    "criminal_id": match.get("criminal_id"),
                    "name": match.get("full_name", "Unknown"),
                    "similarity": match.get("similarity", 0),
                    "wanted_status": match.get("wanted_status"),
                    "danger_level": match.get("danger_level"),
                })

        elif tool_key == "fingerprint_match" and output.get("matches_found", 0) > 0:
            for match in output.get("matches", []):
                criminal_matches.append({
                    "match_type": "fingerprint",
                    "criminal_id": match.get("criminal_id"),
                    "name": match.get("full_name", "Unknown"),
                    "similarity": match.get("similarity", 0),
                })

        elif tool_key == "dna_search" and output.get("matches_found", 0) > 0:
            for match in output.get("matches", []):
                criminal_matches.append({
                    "match_type": "dna",
                    "criminal_id": match.get("criminal_id"),
                    "name": match.get("full_name", "Unknown"),
                    "similarity": match.get("match_percentage", 0),
                })

        elif tool_key == "license_plate_ocr" and output.get("plates_detected", 0) > 0:
            for plate in output.get("plates", []):
                plate_text = plate.get("text", "").replace(" ", "").upper()
                if not plate_text:
                    continue
                stmt = (
                    select(CriminalVehicle, CriminalProfile)
                    .join(CriminalProfile, CriminalVehicle.criminal_id == CriminalProfile.id)
                    .where(CriminalVehicle.registration_number.ilike(f"%{plate_text}%"))
                )
                result_rows = await db.execute(stmt)
                for vehicle, profile in result_rows.all():
                    criminal_matches.append({
                        "match_type": "vehicle_plate",
                        "criminal_id": profile.criminal_id,
                        "name": profile.full_name,
                        "plate_number": vehicle.registration_number,
                        "vehicle_info": f"{vehicle.make or ''} {vehicle.model or ''} ({vehicle.color or ''})".strip(),
                        "wanted_status": profile.wanted_status.value if profile.wanted_status else None,
                    })

    seen = set()
    unique_matches = []
    for m in criminal_matches:
        key = (m.get("criminal_id"), m.get("match_type"))
        if key not in seen:
            seen.add(key)
            unique_matches.append(m)

    return unique_matches


async def generate_investigation_report(
    classification: dict,
    tool_results: list[dict],
    criminal_matches: list[dict],
    user_message: str | None,
    original_filename: str,
) -> str:
    """Generate investigation report using LLM (Gemini or OpenRouter fallback)."""
    try:
        from app.ai.llm_provider import has_any_llm_key, generate_text

        if not has_any_llm_key():
            return _build_fallback_report(classification, tool_results, criminal_matches, original_filename)

        tool_summaries = []
        for r in tool_results:
            if r["status"] == "completed" and r.get("output_data"):
                output_str = json.dumps(r["output_data"], default=str)[:3000]
                tool_summaries.append(f"**{r['tool_key']}** (confidence: {r.get('confidence', 'N/A')}):\n{output_str}")
            elif r["status"] == "failed":
                tool_summaries.append(f"**{r['tool_key']}**: FAILED - {r.get('error', 'Unknown error')}")

        criminal_section = ""
        if criminal_matches:
            criminal_section = "\n\nCRIMINAL DATABASE MATCHES:\n"
            for m in criminal_matches:
                criminal_section += f"- {m['name']} (ID: {m.get('criminal_id')}) via {m['match_type']}, similarity: {m.get('similarity', 'N/A')}\n"

        prompt = f"""You are a senior forensic investigation analyst for CrimeGPT, an AI police investigation system.

Based on the forensic tool execution results below, generate a comprehensive investigation report in markdown format.

EVIDENCE FILE: {original_filename}
CLASSIFICATION: {classification['type']} (confidence: {classification['confidence']})

TOOL RESULTS:
{chr(10).join(tool_summaries)}
{criminal_section}

{'USER QUESTION: ' + user_message if user_message else 'The officer uploaded evidence for automatic investigation.'}

Generate a professional investigation report with these sections:
## Evidence Summary
## Analysis Results
## Key Findings
## Criminal Intelligence (if matches found)
## Recommendations
## Legal Considerations

CRITICAL RULES — SENSITIVE EVIDENCE PIPELINE:
- You MUST only summarize the provided tool outputs above. Do NOT invent, hallucinate, or add information not present in the structured data.
- NEVER fabricate evidence, names, descriptions, or details not found by the forensic tools.
- If a finding is referenced, it MUST appear in the TOOL RESULTS section above.
- Only report what the forensic tools actually found — nothing more.
- State confidence levels for all findings exactly as reported by tools.
- If a tool failed, note it and suggest re-running.
- Do NOT speculate about identity, motive, or guilt.
- Be concise but thorough.
- Use bullet points for clarity."""

        text = await asyncio.to_thread(generate_text, prompt, 0.3, 2048)
        return text

    except Exception as e:
        logger.error(f"LLM report generation failed: {e}")
        return _build_fallback_report(classification, tool_results, criminal_matches, original_filename)


def _build_fallback_report(
    classification: dict,
    tool_results: list[dict],
    criminal_matches: list[dict],
    original_filename: str,
) -> str:
    """Build a structured report without AI when Gemini is unavailable."""
    lines = [
        "## Evidence Summary",
        f"- **File:** {original_filename}",
        f"- **Classification:** {classification['type']}",
        f"- **Confidence:** {classification['confidence']}",
        "",
        "## Analysis Results",
    ]

    for r in tool_results:
        status_icon = "+" if r["status"] == "completed" else "x"
        lines.append(f"- [{status_icon}] **{r['tool_key']}**: {r['status']}")
        if r["status"] == "completed" and r.get("output_data"):
            data = r["output_data"]
            for key in list(data.keys())[:5]:
                val = data[key]
                if isinstance(val, (str, int, float, bool)):
                    lines.append(f"  - {key}: {val}")
        elif r.get("error"):
            lines.append(f"  - Error: {r['error']}")

    if criminal_matches:
        lines.append("")
        lines.append("## Criminal Intelligence Matches")
        for m in criminal_matches:
            lines.append(f"- **{m['name']}** (ID: {m.get('criminal_id')}) — {m['match_type']}")

    lines.append("")
    lines.append("## Recommendations")
    lines.append("- Review tool outputs above for investigative leads")
    lines.append("- AI-powered analysis unavailable — consider re-running when Gemini API is accessible")

    return "\n".join(lines)


async def run_investigation(
    file_path: str,
    original_filename: str,
    user_message: str | None,
    user_id: int,
    case_id: int | None,
    db: AsyncSession,
    evidence_id: int | None = None,
) -> AsyncGenerator[dict, None]:
    """
    IEAE-Enhanced investigation pipeline as an async generator yielding SSE events.

    Pipeline:
    1. Rules-based classification (fast)
    2. AI-enhanced classification (if confidence < 0.8)
    3. Intelligent tool planning (AI planner)
    4. Multi-pass tool execution (parallel groups)
    5. Evidence checklist generation
    6. Completeness scoring
    7. Investigation memory storage
    8. Cross-evidence correlation
    9. Criminal intelligence search
    10. LLM report generation (fact-only)
    11. Final summary with all IEAE data
    """
    from app.services.evidence_completeness_service import generate_checklist, calculate_completeness
    from app.services.investigation_memory_service import (
        store_investigation_findings, correlate_with_case_memory,
    )

    # Step 1: Rules-based classification
    classification = classify_evidence(file_path, original_filename)
    yield {"event": "classification", "data": classification}

    # Step 2: AI-enhanced classification (IEAE Feature 1)
    classification = await classify_evidence_with_ai(file_path, classification)
    if classification.get("ai_enhanced"):
        yield {"event": "ai_classification", "data": classification}

    # Step 3: Static tool plan
    base_plan = get_tools_for_classification(classification)

    # Step 4: AI-enhanced planning (IEAE Feature 2)
    plan = await plan_tools_with_ai(classification, base_plan)
    yield {"event": "plan", "data": {
        "tools_selected": plan["tools_selected"],
        "tools_skipped": plan["tools_skipped"][:5],
        "evidence_type": plan["evidence_type"],
        "ai_enhanced": plan.get("ai_enhanced", False),
        "ai_reasoning": plan.get("ai_reasoning", ""),
        "additional_tools": plan.get("additional_tools", []),
    }}

    # Step 5: Multi-pass tool execution (IEAE Feature 3)
    all_results = []
    pass_number = 0
    for group in plan["parallel_groups"]:
        if not group:
            continue

        for tool_key in group:
            yield {"event": "tool_start", "data": {"tool_key": tool_key}}

        tasks = [
            execute_single_tool(tool_key, file_path, user_id, case_id)
            for tool_key in group
        ]
        group_results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(group_results):
            if isinstance(result, Exception):
                r = {
                    "tool_key": group[i],
                    "execution_id": None,
                    "status": "failed",
                    "confidence": None,
                    "execution_time_ms": 0,
                    "output_data": None,
                    "error": str(result)[:200],
                }
            else:
                r = result
            all_results.append(r)
            pass_number += 1

            yield {"event": "tool_complete", "data": {
                "tool_key": r["tool_key"],
                "execution_id": r.get("execution_id"),
                "status": r["status"],
                "confidence": r.get("confidence"),
                "execution_time_ms": r.get("execution_time_ms"),
            }}

            yield {"event": "pass_complete", "data": {
                "pass_number": pass_number,
                "pass_name": TOOL_DISPLAY_NAMES.get(r["tool_key"], r["tool_key"]),
                "tool_key": r["tool_key"],
                "status": r["status"],
                "confidence": r.get("confidence"),
                "findings_summary": _summarize_findings(r),
                "execution_time_ms": r.get("execution_time_ms", 0),
            }}

    # Step 6: Generate evidence checklist (IEAE Feature 4)
    checklist = generate_checklist(all_results, plan["evidence_type"])
    yield {"event": "checklist", "data": checklist}

    # Step 7: Calculate completeness (IEAE Feature 5)
    has_correlations = False
    completeness = calculate_completeness(
        all_results, plan["evidence_type"], checklist, has_correlations
    )
    yield {"event": "completeness", "data": completeness}

    # Step 8: Store investigation memory (IEAE Feature 6)
    correlations = []
    if case_id and evidence_id:
        try:
            findings_stored = await store_investigation_findings(
                case_id, evidence_id, all_results, db
            )
            if findings_stored:
                yield {"event": "memory_updated", "data": {
                    "findings_count": len(findings_stored),
                    "types": list(set(f["type"] for f in findings_stored)),
                }}

            # Step 9: Cross-evidence correlation (IEAE Feature 7)
            correlations = await correlate_with_case_memory(
                case_id, evidence_id, findings_stored, db
            )
            if correlations:
                has_correlations = True
                yield {"event": "correlations", "data": {
                    "correlations": correlations,
                    "total_links": len(correlations),
                }}
                completeness = calculate_completeness(
                    all_results, plan["evidence_type"], checklist, True
                )

            await db.commit()
        except Exception as e:
            logger.error(f"Investigation memory/correlation failed: {e}")
            await db.rollback()

    # Step 10: Criminal intelligence search
    yield {"event": "criminal_search_start", "data": {}}
    criminal_matches = await search_criminal_intelligence(all_results, db)
    if criminal_matches:
        yield {"event": "criminal_matches", "data": {"matches": criminal_matches}}

    # Step 11: IIDSE — Hypothesis generation & contradiction detection
    hypotheses_data = {}
    contradictions_data = {}
    confidence_data = {}
    try:
        from app.services.hypothesis_service import generate_hypotheses
        from app.services.contradiction_service import detect_contradictions, build_confidence_dashboard

        hypotheses_data = await generate_hypotheses(
            case_id or 0, all_results, criminal_matches, correlations,
            classification, original_filename, db,
        )
        yield {"event": "hypotheses", "data": hypotheses_data}

        contradictions_data = await detect_contradictions(all_results, criminal_matches)
        confidence_data = build_confidence_dashboard(
            all_results, criminal_matches,
            contradictions_data.get("contradictions", []),
            hypotheses_data.get("hypotheses"),
        )
        yield {"event": "contradictions", "data": contradictions_data}
        yield {"event": "confidence_dashboard", "data": confidence_data}
    except Exception as e:
        logger.warning(f"IIDSE hypothesis/contradiction step failed: {e}")

    # Step 12: Generate report (IEAE Feature 8 - sensitive pipeline safeguards)
    yield {"event": "report_start", "data": {}}
    report = await generate_investigation_report(
        classification, all_results, criminal_matches, user_message, original_filename
    )
    yield {"event": "report_complete", "data": {"report": report}}

    # Step 13: Final summary with IEAE + IIDSE data
    yield {"event": "complete", "data": {
        "classification": classification,
        "tool_results": [
            {
                "tool_key": r["tool_key"],
                "execution_id": r.get("execution_id"),
                "status": r["status"],
                "confidence": r.get("confidence"),
                "execution_time_ms": r.get("execution_time_ms"),
                "error": r.get("error"),
            }
            for r in all_results
        ],
        "criminal_matches": criminal_matches,
        "report": report,
        "checklist": checklist,
        "completeness": completeness,
        "correlations": correlations,
        "hypotheses": hypotheses_data.get("hypotheses", []),
        "contradictions": contradictions_data.get("contradictions", []),
        "confidence_dashboard": confidence_data,
    }}


async def handle_followup_message(
    session_messages: list,
    user_message: str,
    attachments: list[dict] | None,
) -> str:
    """Handle a follow-up question using conversation history."""
    try:
        from app.ai.llm_provider import has_any_llm_key, generate_text

        if not has_any_llm_key():
            return "AI analysis unavailable. Please ensure GEMINI_API_KEY or OPENROUTER_API_KEY is configured."

        context_parts = []
        for msg in session_messages[-10:]:
            role_label = "Officer" if msg.get("role") == "user" else "CrimeGPT"
            content = msg.get("content", "")[:2000]
            if msg.get("tool_executions"):
                content += f"\n[Tool results: {len(msg['tool_executions'])} tools executed]"
            context_parts.append(f"{role_label}: {content}")

        prompt = f"""You are CrimeGPT, an AI forensic investigation copilot for police officers.

CONVERSATION HISTORY:
{chr(10).join(context_parts)}

CURRENT QUESTION FROM OFFICER:
{user_message}

Respond based on the evidence and tool results from the conversation history.
CRITICAL: Never fabricate evidence. Only reference actual tool outputs from the conversation.
Be concise, professional, and actionable."""

        text = await asyncio.to_thread(generate_text, prompt, 0.3, 2048)
        return text

    except Exception as e:
        logger.error(f"Follow-up generation failed: {e}")
        return f"I'm unable to process your question at the moment. Error: {str(e)[:100]}"
