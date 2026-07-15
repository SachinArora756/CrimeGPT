"""Executive Investigation Summary — professional report generation with human-in-the-loop markers."""

import json
import asyncio
import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.forensic_toolkit import ForensicToolExecution, ExecutionStatus
from app.models.evidence import Evidence

logger = logging.getLogger(__name__)

EXECUTIVE_SUMMARY_PROMPT = """You are a senior investigation report writer for CrimeGPT.

Generate a professional Executive Investigation Summary based on the data below.

CASE ID: {case_id}
EVIDENCE ANALYZED: {evidence_count} items
TOOL EXECUTIONS: {execution_count} analyses

HYPOTHESES:
{hypotheses_section}

EVIDENCE SUMMARY:
{evidence_section}

CONTRADICTIONS:
{contradictions_section}

CONFIDENCE SCORES:
{confidence_section}

CORRELATIONS:
{correlations_section}

Generate a comprehensive report with these exact sections:

## Executive Summary
(2-3 sentence overview of the investigation status)

## Evidence Summary
(Bullet points of all evidence analyzed and key findings)

## Investigation Hypotheses
(Numbered list with confidence scores — mark each as "AI-Assisted, Requires Verification")

## Supporting Evidence
(What evidence supports each hypothesis)

## Contradictions & Inconsistencies
(Any conflicting evidence found)

## Risk Assessment
(Assessment of evidence strength and case risks)

## Confidence Scores
(Per-category confidence breakdown)

## Recommended Actions
(Prioritized next investigative steps)

## Legal References
(Applicable BNS/BNSS sections if identifiable)

## Outstanding Tasks
(What still needs to be done)

CRITICAL RULES:
- Every finding must be marked as "AI-Assisted — Requires Human Verification"
- NEVER declare guilt or accuse anyone
- NEVER fabricate information not in the data
- Use objective, professional language
- Reference specific evidence items by name
- Include confidence percentages for all claims"""


async def generate_executive_summary(
    case_id: int,
    hypotheses: dict,
    contradictions: dict,
    confidence_dashboard: dict,
    completeness: dict,
    correlations: list[dict],
    db: AsyncSession,
) -> dict:
    """Generate a full executive investigation summary report."""
    try:
        from app.ai.llm_provider import has_any_llm_key, generate_text

        evidence_stmt = select(Evidence).where(Evidence.case_id == case_id)
        evidence_result = await db.execute(evidence_stmt)
        evidence_items = evidence_result.scalars().all()

        exec_stmt = (
            select(ForensicToolExecution)
            .where(ForensicToolExecution.case_id == case_id)
            .where(ForensicToolExecution.status == ExecutionStatus.COMPLETED)
        )
        exec_result = await db.execute(exec_stmt)
        executions = exec_result.scalars().all()

        if not has_any_llm_key():
            return _build_fallback_summary(
                case_id, evidence_items, executions, hypotheses, contradictions,
                confidence_dashboard, completeness, correlations,
            )

        hypotheses_list = hypotheses.get("hypotheses", [])
        hypotheses_section = "\n".join(
            f"- H{h.get('id', i+1)}: {h.get('title', 'Untitled')} (confidence: {h.get('confidence', 0)}%) — {h.get('description', '')[:200]}"
            for i, h in enumerate(hypotheses_list)
        ) or "No hypotheses generated yet."

        evidence_section = "\n".join(
            f"- {ev.original_filename} ({ev.file_type}, {ev.file_size} bytes)"
            for ev in evidence_items[:20]
        ) or "No evidence uploaded."

        contradiction_list = contradictions.get("contradictions", [])
        contradictions_section = "\n".join(
            f"- [{c.get('severity', 'unknown')}] {c.get('description', 'N/A')}"
            for c in contradiction_list
        ) or "No contradictions detected."

        confidence_section = json.dumps(confidence_dashboard.get("category_scores", {}), indent=2, default=str)

        correlations_section = "\n".join(
            f"- {c.get('correlation_type', '?')}: confidence {c.get('confidence', 0):.0%}"
            for c in correlations[:10]
        ) or "No cross-evidence correlations."

        prompt = EXECUTIVE_SUMMARY_PROMPT.format(
            case_id=case_id,
            evidence_count=len(evidence_items),
            execution_count=len(executions),
            hypotheses_section=hypotheses_section,
            evidence_section=evidence_section,
            contradictions_section=contradictions_section,
            confidence_section=confidence_section,
            correlations_section=correlations_section,
        )

        report_text = await asyncio.to_thread(generate_text, prompt, 0.3, 4000)

        return {
            "report": report_text,
            "generated_at": datetime.utcnow().isoformat(),
            "metadata": {
                "case_id": case_id,
                "evidence_count": len(evidence_items),
                "execution_count": len(executions),
                "hypotheses_count": len(hypotheses_list),
                "contradictions_count": len(contradiction_list),
                "overall_confidence": confidence_dashboard.get("overall_investigation_confidence", 0),
            },
            "disclaimer": "AI-Generated Report — All findings require human verification before any legal action.",
            "human_verification_required": True,
        }

    except Exception as e:
        logger.error(f"Executive summary generation failed: {e}")
        return {
            "report": f"## Error\nFailed to generate executive summary: {str(e)[:200]}",
            "generated_at": datetime.utcnow().isoformat(),
            "metadata": {"case_id": case_id, "error": True},
            "disclaimer": "AI-Generated Report — All findings require human verification.",
            "human_verification_required": True,
        }


async def reanalyze_evidence(case_id: int, evidence_id: int, db: AsyncSession) -> dict:
    """Continuous Learning: Re-analyze evidence with current models (for when models are updated)."""
    evidence_stmt = select(Evidence).where(Evidence.id == evidence_id, Evidence.case_id == case_id)
    evidence_result = await db.execute(evidence_stmt)
    evidence = evidence_result.scalar_one_or_none()

    if not evidence:
        return {"status": "error", "message": "Evidence not found"}

    prev_exec_stmt = (
        select(ForensicToolExecution)
        .where(ForensicToolExecution.evidence_id == evidence_id)
        .where(ForensicToolExecution.status == ExecutionStatus.COMPLETED)
    )
    prev_result = await db.execute(prev_exec_stmt)
    previous_tools = [exe.tool_key for exe in prev_result.scalars().all()]

    return {
        "status": "ready",
        "evidence_id": evidence_id,
        "evidence_file": evidence.original_filename,
        "previous_analyses": previous_tools,
        "message": f"Evidence ready for re-analysis. Previously analyzed with {len(previous_tools)} tools: {', '.join(previous_tools[:10])}",
        "reanalysis_supported": True,
    }


def _build_fallback_summary(
    case_id, evidence_items, executions, hypotheses, contradictions,
    confidence_dashboard, completeness, correlations,
) -> dict:
    lines = [
        "## Executive Summary",
        f"Case #{case_id} — AI investigation analysis complete.",
        f"{len(evidence_items)} evidence items analyzed with {len(executions)} forensic tool executions.",
        "",
        "## Evidence Summary",
    ]
    for ev in evidence_items[:10]:
        lines.append(f"- {ev.original_filename} ({ev.file_type})")

    lines.append("")
    lines.append("## Investigation Hypotheses")
    for h in hypotheses.get("hypotheses", []):
        lines.append(f"- **{h.get('title', 'Untitled')}** (confidence: {h.get('confidence', 0)}%) — AI-Assisted, Requires Verification")

    lines.append("")
    lines.append("## Contradictions")
    contradiction_list = contradictions.get("contradictions", [])
    if contradiction_list:
        for c in contradiction_list:
            lines.append(f"- [{c.get('severity', '?')}] {c.get('description', 'N/A')}")
    else:
        lines.append("- No contradictions detected")

    lines.append("")
    lines.append("## Confidence Scores")
    lines.append(f"- Overall: {confidence_dashboard.get('overall_investigation_confidence', 0):.0f}%")

    lines.append("")
    lines.append("## Recommended Actions")
    for action in hypotheses.get("recommended_actions", [])[:5]:
        lines.append(f"- [{action.get('priority', 'medium')}] {action.get('action', 'N/A')}")

    lines.append("")
    lines.append("---")
    lines.append("*AI-Generated Report — All findings require human verification before any legal action.*")

    return {
        "report": "\n".join(lines),
        "generated_at": datetime.utcnow().isoformat(),
        "metadata": {"case_id": case_id, "fallback": True},
        "disclaimer": "AI-Generated Report — All findings require human verification.",
        "human_verification_required": True,
    }
