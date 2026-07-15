"""Investigation Hypothesis Engine — generates, scores, and explains investigation hypotheses."""

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

HYPOTHESIS_PROMPT = """You are a senior criminal investigator AI assistant for CrimeGPT.

Based on the forensic analysis results below, generate investigation hypotheses.

CASE EVIDENCE SUMMARY:
{evidence_summary}

FORENSIC TOOL RESULTS:
{tool_results}

CRIMINAL DATABASE MATCHES:
{criminal_matches}

CROSS-EVIDENCE CORRELATIONS:
{correlations}

Generate 2-4 investigation hypotheses. Each hypothesis must be:
1. Based ONLY on the evidence provided — never fabricate
2. Clearly labeled as "AI-Assisted Hypothesis — Requires Human Verification"
3. Scored by confidence (0-100)

Respond with ONLY a JSON object:
{{
  "hypotheses": [
    {{
      "id": 1,
      "title": "brief title",
      "description": "detailed hypothesis explanation",
      "confidence": 85,
      "supporting_evidence": ["evidence item 1", "evidence item 2"],
      "conflicting_evidence": ["anything that contradicts this"],
      "reasoning": "why this hypothesis is plausible",
      "suspects": ["named suspects from criminal matches only"],
      "key_factors": ["factor1", "factor2"]
    }}
  ],
  "recommended_actions": [
    {{
      "action": "what to do next",
      "priority": "high/medium/low",
      "reason": "why this action matters"
    }}
  ]
}}

CRITICAL: Never accuse anyone. Never declare guilt. Label everything as hypothesis requiring verification."""

NEXT_STEPS_PROMPT = """Based on the investigation evidence and hypotheses below, recommend the next investigative actions.

EVIDENCE ANALYZED:
{evidence_summary}

CURRENT HYPOTHESES:
{hypotheses_summary}

MISSING ANALYSES:
{missing_analyses}

Generate 5-8 recommended next steps. Each should be actionable and explain why.

Respond with ONLY a JSON object:
{{
  "next_steps": [
    {{
      "action": "specific action to take",
      "priority": "high/medium/low",
      "reason": "why this will advance the investigation",
      "category": "forensic/interview/surveillance/document/digital/financial"
    }}
  ]
}}"""


async def generate_hypotheses(
    case_id: int,
    tool_results: list[dict],
    criminal_matches: list[dict],
    correlations: list[dict],
    classification: dict,
    original_filename: str,
    db: AsyncSession,
) -> dict:
    """Generate investigation hypotheses from evidence analysis results."""
    try:
        from app.ai.llm_provider import has_any_llm_key, generate_text

        if not has_any_llm_key():
            return _build_fallback_hypotheses(tool_results, criminal_matches)

        evidence_summary = _build_evidence_summary(tool_results, classification, original_filename)
        tool_summary = _build_tool_summary(tool_results)
        criminal_summary = _build_criminal_summary(criminal_matches)
        correlation_summary = _build_correlation_summary(correlations)

        prompt = HYPOTHESIS_PROMPT.format(
            evidence_summary=evidence_summary,
            tool_results=tool_summary,
            criminal_matches=criminal_summary,
            correlations=correlation_summary,
        )

        response = await asyncio.to_thread(generate_text, prompt, 0.4, 3000)
        parsed = json.loads(response.strip().strip("```json").strip("```").strip())

        hypotheses = parsed.get("hypotheses", [])
        for h in hypotheses:
            h["status"] = "ai_generated"
            h["verification_required"] = True
            h["generated_at"] = datetime.utcnow().isoformat()

        recommended_actions = parsed.get("recommended_actions", [])

        return {
            "hypotheses": hypotheses,
            "recommended_actions": recommended_actions,
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "disclaimer": "AI-Assisted Hypotheses — Requires Human Verification",
                "evidence_count": len(tool_results),
                "criminal_matches_count": len(criminal_matches),
            },
        }

    except Exception as e:
        logger.error(f"Hypothesis generation failed: {e}")
        return _build_fallback_hypotheses(tool_results, criminal_matches)


async def generate_next_steps(
    case_id: int,
    hypotheses: list[dict],
    tool_results: list[dict],
    missing_analyses: list[str],
    db: AsyncSession,
) -> list[dict]:
    """Generate intelligent next-step recommendations."""
    try:
        from app.ai.llm_provider import has_any_llm_key, generate_text

        if not has_any_llm_key():
            return _build_fallback_next_steps(tool_results, missing_analyses)

        evidence_summary = "\n".join(
            f"- {r['tool_key']}: {r['status']} (confidence: {r.get('confidence', 'N/A')})"
            for r in tool_results
        )
        hypotheses_summary = "\n".join(
            f"- Hypothesis {h.get('id', i+1)}: {h.get('title', 'Untitled')} (confidence: {h.get('confidence', 0)}%)"
            for i, h in enumerate(hypotheses)
        )
        missing_str = "\n".join(f"- {m}" for m in missing_analyses) if missing_analyses else "None identified"

        prompt = NEXT_STEPS_PROMPT.format(
            evidence_summary=evidence_summary,
            hypotheses_summary=hypotheses_summary,
            missing_analyses=missing_str,
        )

        response = await asyncio.to_thread(generate_text, prompt, 0.3, 1500)
        parsed = json.loads(response.strip().strip("```json").strip("```").strip())

        return parsed.get("next_steps", [])

    except Exception as e:
        logger.error(f"Next steps generation failed: {e}")
        return _build_fallback_next_steps(tool_results, missing_analyses)


async def get_case_hypotheses(case_id: int, db: AsyncSession) -> dict:
    """Retrieve all evidence and generate hypotheses for an entire case."""
    evidence_stmt = select(Evidence).where(Evidence.case_id == case_id)
    evidence_result = await db.execute(evidence_stmt)
    evidence_items = evidence_result.scalars().all()

    exec_stmt = (
        select(ForensicToolExecution)
        .where(ForensicToolExecution.case_id == case_id)
        .where(ForensicToolExecution.status == ExecutionStatus.COMPLETED)
        .order_by(ForensicToolExecution.created_at.desc())
    )
    exec_result = await db.execute(exec_stmt)
    executions = exec_result.scalars().all()

    tool_results = []
    criminal_matches = []
    for exe in executions:
        result = {
            "tool_key": exe.tool_key,
            "status": "completed",
            "confidence": exe.confidence_score,
            "output_data": exe.output_data,
            "execution_time_ms": exe.execution_time_ms,
        }
        tool_results.append(result)

        if exe.tool_key == "face_recognize" and exe.output_data:
            for match in exe.output_data.get("matches", []):
                criminal_matches.append({
                    "match_type": "face_recognition",
                    "criminal_id": match.get("criminal_id"),
                    "name": match.get("full_name", "Unknown"),
                    "similarity": match.get("similarity", 0),
                })

    corr_stmt = select(EvidenceCorrelation).where(EvidenceCorrelation.case_id == case_id)
    corr_result = await db.execute(corr_stmt)
    correlations = [
        {
            "correlation_type": c.correlation_type,
            "confidence": c.confidence,
            "details": c.details,
        }
        for c in corr_result.scalars().all()
    ]

    classification = {"type": "case_aggregate", "confidence": 1.0}

    return await generate_hypotheses(
        case_id, tool_results, criminal_matches, correlations,
        classification, f"Case #{case_id} (all evidence)", db,
    )


def _build_evidence_summary(tool_results: list[dict], classification: dict, filename: str) -> str:
    completed = [r for r in tool_results if r["status"] == "completed"]
    return (
        f"File: {filename}\n"
        f"Type: {classification.get('type', 'unknown')}\n"
        f"Tools executed: {len(tool_results)} ({len(completed)} successful)\n"
    )


def _build_tool_summary(tool_results: list[dict]) -> str:
    lines = []
    for r in tool_results:
        if r["status"] == "completed" and r.get("output_data"):
            output_str = json.dumps(r["output_data"], default=str)[:1500]
            lines.append(f"{r['tool_key']} (conf: {r.get('confidence', 'N/A')}): {output_str}")
    return "\n".join(lines[:15]) or "No tool results available"


def _build_criminal_summary(criminal_matches: list[dict]) -> str:
    if not criminal_matches:
        return "No criminal database matches found."
    lines = [f"- {m.get('name', 'Unknown')} via {m.get('match_type', '?')} (similarity: {m.get('similarity', 'N/A')})" for m in criminal_matches]
    return "\n".join(lines)


def _build_correlation_summary(correlations: list[dict]) -> str:
    if not correlations:
        return "No cross-evidence correlations found."
    lines = [f"- {c.get('correlation_type', '?')} (confidence: {c.get('confidence', 0):.0%})" for c in correlations]
    return "\n".join(lines)


def _build_fallback_hypotheses(tool_results: list[dict], criminal_matches: list[dict]) -> dict:
    hypotheses = []
    if criminal_matches:
        for i, match in enumerate(criminal_matches[:3]):
            hypotheses.append({
                "id": i + 1,
                "title": f"Suspect: {match.get('name', 'Unknown')}",
                "description": f"Criminal database match via {match.get('match_type', 'unknown')} with similarity {match.get('similarity', 'N/A')}",
                "confidence": int(float(match.get("similarity", 50)) * 100) if isinstance(match.get("similarity"), float) and match["similarity"] <= 1 else int(match.get("similarity", 50)),
                "supporting_evidence": [f"{match.get('match_type')} match"],
                "conflicting_evidence": [],
                "reasoning": "Direct match found in criminal database",
                "suspects": [match.get("name", "Unknown")],
                "key_factors": [match.get("match_type", "database match")],
                "status": "ai_generated",
                "verification_required": True,
            })
    else:
        hypotheses.append({
            "id": 1,
            "title": "Unknown Subject",
            "description": "No criminal database matches found. Further investigation required.",
            "confidence": 20,
            "supporting_evidence": [f"{len(tool_results)} forensic analyses completed"],
            "conflicting_evidence": [],
            "reasoning": "Insufficient evidence for specific suspect identification",
            "suspects": [],
            "key_factors": ["no database matches"],
            "status": "ai_generated",
            "verification_required": True,
        })

    return {
        "hypotheses": hypotheses,
        "recommended_actions": _build_fallback_next_steps(tool_results, []),
        "metadata": {
            "generated_at": datetime.utcnow().isoformat(),
            "disclaimer": "AI-Assisted Hypotheses — Requires Human Verification",
            "fallback": True,
        },
    }


def _build_fallback_next_steps(tool_results: list[dict], missing_analyses: list[str]) -> list[dict]:
    steps = []
    executed_tools = {r["tool_key"] for r in tool_results if r["status"] == "completed"}

    if "face_recognize" not in executed_tools:
        steps.append({"action": "Run face recognition against criminal database", "priority": "high", "reason": "May identify known suspects", "category": "forensic"})
    if "fingerprint_match" not in executed_tools:
        steps.append({"action": "Search fingerprint database", "priority": "high", "reason": "Fingerprint matches provide strong identification", "category": "forensic"})
    steps.append({"action": "Interview witnesses from the scene", "priority": "high", "reason": "Witness statements corroborate forensic evidence", "category": "interview"})
    steps.append({"action": "Check nearby CCTV footage", "priority": "medium", "reason": "Video evidence may capture suspect movement", "category": "surveillance"})
    steps.append({"action": "Obtain Call Detail Records for the area", "priority": "medium", "reason": "CDR can place suspects at the scene", "category": "digital"})
    if "dna_search" not in executed_tools:
        steps.append({"action": "Collect and analyze DNA evidence", "priority": "medium", "reason": "DNA provides conclusive identification", "category": "forensic"})
    steps.append({"action": "Check financial transaction records", "priority": "low", "reason": "Financial trails may reveal motive", "category": "financial"})

    for missing in missing_analyses[:3]:
        steps.append({"action": missing, "priority": "medium", "reason": "Identified as missing analysis", "category": "forensic"})

    return steps[:8]
