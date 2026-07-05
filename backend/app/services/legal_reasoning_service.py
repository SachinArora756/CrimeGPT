import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.case_context_builder import build_case_context
from app.ai.rag.retriever import multi_query_search, hybrid_search
from app.models.legal_recommendation import LegalRecommendation, RecommendationStatus


LEGAL_REASONING_PROMPT = """You are an expert Indian criminal law analyst assisting police investigators.

Based on the case details and retrieved legal provisions below, provide structured legal recommendations.

CASE CONTEXT:
{case_summary}

RETRIEVED LEGAL PROVISIONS:
{provisions_text}

INSTRUCTIONS:
1. Only recommend sections from BNS 2023, BNSS 2023, BSA 2023, or Constitution of India.
2. Each recommendation MUST cite specific evidence or facts from the case that support it.
3. Assign confidence scores:
   - 0.3-0.4: Weak circumstantial connection
   - 0.5-0.6: Moderate — elements partially established
   - 0.7-0.8: Strong — direct evidence supports most elements
   - 0.9-1.0: Very strong — conclusive evidence for all elements
4. Distinguish primary charges (is_primary: true) from alternative/lesser charges.
5. Identify evidence gaps — what additional evidence would strengthen the case.
6. Provide procedural notes relevant to the investigation stage.

Respond ONLY with valid JSON in this exact format:
{{
  "recommendations": [
    {{
      "section": "Section number",
      "act": "BNS/BNSS/BSA/Constitution",
      "title": "Section title",
      "explanation": "Why this section applies based on the facts",
      "supporting_evidence": ["List of specific evidence/facts supporting this"],
      "confidence": 0.7,
      "punishment_range": "Applicable punishment",
      "is_primary": true
    }}
  ],
  "procedural_notes": ["Relevant BNSS procedural requirements"],
  "evidence_gaps": ["What additional evidence is needed"]
}}"""


async def generate_recommendations(
    db: AsyncSession,
    case_id: int,
    user_id: int,
    focus_area: str | None = None,
) -> LegalRecommendation:
    ctx = await build_case_context(db, case_id)
    rag_queries = ctx.generate_rag_queries(focus_area)

    provisions = await multi_query_search(
        queries=rag_queries,
        top_k_per_query=5,
        deduplicate=True,
    )

    if ctx.evidence_tags:
        keyword_results = await hybrid_search(
            query=ctx.description[:200] if ctx.description else "criminal offense",
            keywords=ctx.evidence_tags[:5],
            top_k=10,
        )
        seen = {p["text"][:100] for p in provisions}
        for kr in keyword_results:
            if kr["text"][:100] not in seen:
                provisions.append(kr)
                seen.add(kr["text"][:100])

    provisions_text = _format_provisions(provisions[:25])
    case_summary = ctx.build_summary()

    llm_response = await _call_llm(case_summary, provisions_text)

    parsed = _parse_llm_response(llm_response, provisions)
    recommendations_data = parsed.get("recommendations", [])
    procedural_notes = parsed.get("procedural_notes", [])
    evidence_gaps = parsed.get("evidence_gaps", [])

    overall_confidence = 0.0
    if recommendations_data:
        confidences = [r.get("confidence", 0.5) for r in recommendations_data]
        overall_confidence = round(sum(confidences) / len(confidences), 2)

    rec = LegalRecommendation(
        case_id=case_id,
        recommendations={
            "recommendations": recommendations_data,
            "procedural_notes": procedural_notes,
            "evidence_gaps": evidence_gaps,
        },
        overall_confidence=overall_confidence,
        status=RecommendationStatus.PENDING_APPROVAL,
        created_by=user_id,
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)
    return rec


async def approve_recommendations(
    db: AsyncSession,
    recommendation: LegalRecommendation,
    approved_sections: list[str],
    notes: str | None,
    officer_id: int,
) -> LegalRecommendation:
    all_sections = [
        r.get("section", "") for r in recommendation.recommendations.get("recommendations", [])
    ]

    if len(approved_sections) == len(all_sections):
        recommendation.status = RecommendationStatus.APPROVED
    elif len(approved_sections) == 0:
        recommendation.status = RecommendationStatus.REJECTED
    else:
        recommendation.status = RecommendationStatus.PARTIALLY_APPROVED

    recommendation.approved_sections = approved_sections
    recommendation.officer_notes = notes
    recommendation.approved_by = officer_id
    recommendation.approved_at = datetime.utcnow()

    await db.commit()
    await db.refresh(recommendation)
    return recommendation


def _format_provisions(provisions: list[dict]) -> str:
    if not provisions:
        return "No provisions retrieved from knowledge base."

    parts = []
    for i, p in enumerate(provisions, 1):
        section = p.get("section_number", "")
        act = p.get("act", "")
        heading = p.get("heading", "")
        text = p.get("text", "")
        punishment = p.get("punishment_range", "")
        category = p.get("offense_category", "")

        header = f"[{i}] {act}"
        if section:
            header += f" Section {section}"
        if heading:
            header += f" - {heading}"
        if category:
            header += f" ({category})"

        entry = f"{header}\n{text[:500]}"
        if punishment:
            entry += f"\nPunishment: {punishment}"
        parts.append(entry)

    return "\n\n".join(parts)


async def _call_llm(case_summary: str, provisions_text: str) -> str:
    if not settings.gemini_api_key:
        return _fallback_response(provisions_text)

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI

        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=settings.gemini_api_key,
            temperature=0.1,
        )

        prompt = LEGAL_REASONING_PROMPT.format(
            case_summary=case_summary[:4000],
            provisions_text=provisions_text[:6000],
        )

        response = await llm.ainvoke(prompt)
        return response.content
    except Exception:
        return _fallback_response(provisions_text)


def _fallback_response(provisions_text: str) -> str:
    return json.dumps({
        "recommendations": [],
        "procedural_notes": ["LLM unavailable. Review retrieved provisions manually."],
        "evidence_gaps": ["Automated analysis not available. Manual review required."],
    })


def _parse_llm_response(response: str, provisions: list[dict]) -> dict:
    try:
        cleaned = response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        parsed = json.loads(cleaned)

        if "recommendations" not in parsed:
            parsed = {"recommendations": [], "procedural_notes": [], "evidence_gaps": []}

        for rec in parsed.get("recommendations", []):
            if "confidence" in rec:
                rec["confidence"] = max(0.0, min(1.0, float(rec["confidence"])))
            if "is_primary" not in rec:
                rec["is_primary"] = True
            if "supporting_evidence" not in rec:
                rec["supporting_evidence"] = []

        return parsed
    except (json.JSONDecodeError, ValueError):
        return {
            "recommendations": [],
            "procedural_notes": ["Failed to parse LLM response. Review provisions manually."],
            "evidence_gaps": [],
        }
