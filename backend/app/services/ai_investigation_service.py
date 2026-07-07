"""
AI Investigation Copilot Service

Orchestrates: Evidence Classification → Tool Planning → Parallel Execution →
Criminal Intelligence Search → LLM Report Generation
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

CRITICAL RULES:
- NEVER fabricate evidence or data
- Only report what the forensic tools actually found
- State confidence levels for all findings
- If a tool failed, note it and suggest alternatives
- Be concise but thorough
- Use bullet points for clarity"""

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
) -> AsyncGenerator[dict, None]:
    """
    Full investigation pipeline as an async generator yielding SSE events.
    """
    # Step 1: Classify
    classification = classify_evidence(file_path, original_filename)
    yield {"event": "classification", "data": classification}

    # Step 2: Plan
    plan = get_tools_for_classification(classification)
    yield {"event": "plan", "data": {
        "tools_selected": plan["tools_selected"],
        "tools_skipped": plan["tools_skipped"][:5],
        "evidence_type": plan["evidence_type"],
    }}

    # Step 3: Execute tools
    all_results = []
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
            yield {"event": "tool_complete", "data": {
                "tool_key": r["tool_key"],
                "execution_id": r.get("execution_id"),
                "status": r["status"],
                "confidence": r.get("confidence"),
                "execution_time_ms": r.get("execution_time_ms"),
            }}

    # Step 4: Criminal intelligence search
    yield {"event": "criminal_search_start", "data": {}}
    criminal_matches = await search_criminal_intelligence(all_results, db)
    if criminal_matches:
        yield {"event": "criminal_matches", "data": {"matches": criminal_matches}}

    # Step 5: Generate report
    yield {"event": "report_start", "data": {}}
    report = await generate_investigation_report(
        classification, all_results, criminal_matches, user_message, original_filename
    )
    yield {"event": "report_complete", "data": {"report": report}}

    # Step 6: Final summary
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
