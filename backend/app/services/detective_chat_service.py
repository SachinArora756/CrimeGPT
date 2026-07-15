"""Enhanced AI Detective Chat — tool-result-aware forensic investigation copilot."""

import json
import asyncio
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.forensic_toolkit import ForensicToolExecution, ExecutionStatus
from app.models.evidence import Evidence
from app.models.investigation_memory import InvestigationMemory, EvidenceCorrelation

logger = logging.getLogger(__name__)

DETECTIVE_SYSTEM_PROMPT = """You are CrimeGPT's AI Detective Copilot — a senior forensic investigation assistant.

YOUR CAPABILITIES:
- Answer investigative questions based on actual tool results
- Explain what each forensic tool found and its significance
- Identify connections between evidence items
- Suggest next investigative actions
- Explain confidence levels and limitations
- Reference applicable BNS/BNSS/IPC/CrPC sections

INVESTIGATION CONTEXT:
Case ID: {case_id}
Evidence Items: {evidence_count}
Forensic Analyses Completed: {analysis_count}
Criminal Matches Found: {criminal_match_count}
Cross-Evidence Correlations: {correlation_count}

FORENSIC TOOL RESULTS (actual findings):
{tool_results_context}

INVESTIGATION MEMORY (key findings):
{memory_context}

CROSS-EVIDENCE CORRELATIONS:
{correlation_context}

CONVERSATION HISTORY:
{conversation_history}

OFFICER'S QUESTION:
{question}

RESPONSE RULES:
1. ONLY reference findings that exist in the tool results above
2. NEVER fabricate evidence, suspects, or findings
3. Mark all AI conclusions with "[AI-Assisted — Requires Verification]"
4. When explaining confidence, cite the specific tool and its confidence score
5. If asked about something not in the evidence, say "This has not been analyzed in the current evidence set"
6. Be concise, professional, and actionable
7. If referencing a suspect, always note they are "a person of interest based on database similarity, NOT confirmed as guilty"
8. When suggesting next steps, be specific and prioritize by impact

Respond in a helpful, professional manner. Use markdown formatting for clarity."""

EXPLAIN_PROMPT = """Based on the following forensic tool result, provide a clear explanation suitable for a police officer:

TOOL: {tool_name}
RESULT:
{tool_output}

Explain:
1. What was found (in plain language)
2. What it means for the investigation
3. Confidence level and limitations
4. What this could lead to next

Keep the explanation under 200 words. Mark findings as "AI-Assisted — Requires Verification"."""


async def enhanced_detective_chat(
    case_id: int | None,
    session_messages: list[dict],
    user_message: str,
    db: AsyncSession,
) -> dict:
    """Handle detective chat with full case context and tool-result awareness."""
    try:
        from app.ai.llm_provider import has_any_llm_key, generate_text

        if not has_any_llm_key():
            return {
                "response": "AI analysis unavailable. Please ensure GEMINI_API_KEY or OPENROUTER_API_KEY is configured.",
                "sources": [],
                "confidence": 0,
            }

        tool_results_context = "No case linked to this session."
        memory_context = "No investigation memory available."
        correlation_context = "No correlations found."
        evidence_count = 0
        analysis_count = 0
        criminal_match_count = 0
        correlation_count = 0
        sources = []

        if case_id:
            evidence_stmt = select(Evidence).where(Evidence.case_id == case_id)
            ev_result = await db.execute(evidence_stmt)
            evidence_items = ev_result.scalars().all()
            evidence_count = len(evidence_items)

            exec_stmt = (
                select(ForensicToolExecution)
                .where(ForensicToolExecution.case_id == case_id)
                .where(ForensicToolExecution.status == ExecutionStatus.COMPLETED)
                .order_by(ForensicToolExecution.created_at.desc())
            )
            exec_result = await db.execute(exec_stmt)
            executions = exec_result.scalars().all()
            analysis_count = len(executions)

            tool_lines = []
            for exe in executions[:20]:
                output_summary = json.dumps(exe.output_data, default=str)[:800] if exe.output_data else "No output"
                tool_lines.append(
                    f"[{exe.tool_key}] (confidence: {exe.confidence_score or 'N/A'}, "
                    f"evidence: {exe.evidence_id}): {output_summary}"
                )
                sources.append({
                    "tool": exe.tool_key,
                    "evidence_id": exe.evidence_id,
                    "confidence": exe.confidence_score,
                })

                if exe.tool_key == "face_recognize" and exe.output_data:
                    criminal_match_count += len(exe.output_data.get("matches", []))

            tool_results_context = "\n".join(tool_lines) if tool_lines else "No analyses completed yet."

            mem_stmt = (
                select(InvestigationMemory)
                .where(InvestigationMemory.case_id == case_id)
                .order_by(InvestigationMemory.created_at.desc())
                .limit(30)
            )
            mem_result = await db.execute(mem_stmt)
            memories = mem_result.scalars().all()

            if memories:
                mem_lines = []
                for m in memories:
                    data_str = json.dumps(m.finding_data, default=str)[:300] if m.finding_data else ""
                    mem_lines.append(f"[{m.finding_type}] key={m.finding_key}: {data_str}")
                memory_context = "\n".join(mem_lines)

            corr_stmt = (
                select(EvidenceCorrelation)
                .where(EvidenceCorrelation.case_id == case_id)
                .order_by(EvidenceCorrelation.confidence.desc())
                .limit(15)
            )
            corr_result = await db.execute(corr_stmt)
            correlations = corr_result.scalars().all()
            correlation_count = len(correlations)

            if correlations:
                corr_lines = [
                    f"Evidence #{c.source_evidence_id} ↔ #{c.target_evidence_id}: "
                    f"{c.correlation_type} (confidence: {c.confidence:.0%})"
                    for c in correlations
                ]
                correlation_context = "\n".join(corr_lines)

        conversation_history = "\n".join(
            f"{'Officer' if m.get('role') == 'user' else 'CrimeGPT'}: {m.get('content', '')[:1500]}"
            for m in session_messages[-8:]
        )

        prompt = DETECTIVE_SYSTEM_PROMPT.format(
            case_id=case_id or "None",
            evidence_count=evidence_count,
            analysis_count=analysis_count,
            criminal_match_count=criminal_match_count,
            correlation_count=correlation_count,
            tool_results_context=tool_results_context,
            memory_context=memory_context,
            correlation_context=correlation_context,
            conversation_history=conversation_history,
            question=user_message,
        )

        response_text = await asyncio.to_thread(generate_text, prompt, 0.3, 2500)

        return {
            "response": response_text,
            "sources": sources[:10],
            "confidence": _estimate_response_confidence(user_message, analysis_count, criminal_match_count),
            "context_used": {
                "evidence_items": evidence_count,
                "tool_results": min(analysis_count, 20),
                "memory_entries": len(memories) if case_id else 0,
                "correlations": correlation_count,
            },
        }

    except Exception as e:
        logger.error(f"Detective chat failed: {e}")
        return {
            "response": f"I'm unable to process your question at the moment. Error: {str(e)[:100]}",
            "sources": [],
            "confidence": 0,
        }


async def explain_tool_result(
    tool_key: str,
    execution_id: int,
    db: AsyncSession,
) -> dict:
    """Provide a detailed explanation of a specific tool's findings."""
    try:
        from app.ai.llm_provider import has_any_llm_key, generate_text

        stmt = select(ForensicToolExecution).where(ForensicToolExecution.id == execution_id)
        result = await db.execute(stmt)
        execution = result.scalar_one_or_none()

        if not execution:
            return {"explanation": "Tool execution not found.", "tool_key": tool_key}

        if not has_any_llm_key():
            return {
                "explanation": _build_fallback_explanation(execution),
                "tool_key": execution.tool_key,
                "confidence": execution.confidence_score,
            }

        output_str = json.dumps(execution.output_data, default=str)[:3000] if execution.output_data else "No output"

        prompt = EXPLAIN_PROMPT.format(
            tool_name=execution.tool_key,
            tool_output=output_str,
        )

        explanation = await asyncio.to_thread(generate_text, prompt, 0.3, 1000)

        return {
            "explanation": explanation,
            "tool_key": execution.tool_key,
            "confidence": execution.confidence_score,
            "execution_time_ms": execution.execution_time_ms,
            "evidence_id": execution.evidence_id,
        }

    except Exception as e:
        logger.error(f"Tool explanation failed: {e}")
        return {"explanation": f"Unable to explain: {str(e)[:100]}", "tool_key": tool_key}


def _estimate_response_confidence(question: str, analysis_count: int, match_count: int) -> float:
    """Estimate how confident the response is based on available data."""
    base = 0.3
    if analysis_count > 0:
        base += min(analysis_count * 0.05, 0.3)
    if match_count > 0:
        base += 0.15
    q_lower = question.lower()
    if any(w in q_lower for w in ("who", "suspect", "identity", "name")):
        if match_count == 0:
            base -= 0.2
    return round(min(max(base, 0.1), 0.95), 2)


def _build_fallback_explanation(execution) -> str:
    """Build a basic explanation without LLM."""
    tool_key = execution.tool_key
    output = execution.output_data or {}

    explanations = {
        "face_detect": f"Detected {output.get('faces_count', 0)} face(s) in the image.",
        "face_recognize": f"Found {len(output.get('matches', []))} match(es) in criminal database.",
        "vehicle_detect": f"Detected {len(output.get('detections', []))} vehicle(s).",
        "weapon_detect": f"Detected {output.get('weapons_detected', 0)} weapon(s).",
        "license_plate_ocr": f"Extracted plate number: {output.get('plate_number', 'N/A')}.",
        "image_ocr": f"Extracted {len(output.get('text', ''))} characters of text.",
        "image_exif": f"EXIF data extracted. GPS: {output.get('gps', 'Not available')}.",
        "fingerprint_match": f"Fingerprint analysis: {output.get('matches_found', 0)} match(es).",
        "crime_scene_analysis": "Crime scene analysis completed.",
    }

    base_explanation = explanations.get(tool_key, f"Tool '{tool_key}' completed.")
    conf = execution.confidence_score
    conf_str = f" Confidence: {conf:.0%}." if conf else ""

    return f"{base_explanation}{conf_str} [AI-Assisted — Requires Verification]"
