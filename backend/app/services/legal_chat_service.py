import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.legal_chat import LegalChatMessage
from app.models.chat import ChatRole
from app.models.legal_recommendation import LegalRecommendation
from app.services.case_context_builder import build_case_context
from app.ai.rag.retriever import search_legal_provisions


LEGAL_FOLLOWUP_PROMPT = """You are CrimeGPT, an expert Indian criminal law assistant helping a police officer.
You are answering follow-up questions about AI-generated legal recommendations for a case.

CASE CONTEXT:
{case_summary}

CURRENT RECOMMENDATIONS:
{recommendations_text}

EVIDENCE GAPS IDENTIFIED:
{evidence_gaps}

PROCEDURAL NOTES:
{procedural_notes}

RELEVANT LEGAL PROVISIONS (from knowledge base):
{rag_context}

PREVIOUS CONVERSATION:
{chat_history}

USER QUESTION: {user_message}

Provide a helpful, precise, and actionable response. Cite specific BNS/BNSS/BSA sections where applicable.
Focus on practical next steps the officer can take. Be concise but thorough."""


async def get_legal_chat_history(
    db: AsyncSession,
    recommendation_id: int,
    limit: int = 50,
    offset: int = 0,
) -> list[LegalChatMessage]:
    result = await db.execute(
        select(LegalChatMessage)
        .where(LegalChatMessage.recommendation_id == recommendation_id)
        .order_by(LegalChatMessage.created_at.asc())
        .offset(offset)
        .limit(limit)
    )
    return list(result.scalars().all())


async def process_legal_chat(
    db: AsyncSession,
    case_id: int,
    recommendation_id: int,
    user_id: int,
    message: str,
) -> LegalChatMessage:
    user_msg = LegalChatMessage(
        case_id=case_id,
        recommendation_id=recommendation_id,
        user_id=user_id,
        role=ChatRole.USER,
        content=message,
    )
    db.add(user_msg)
    await db.flush()

    rec_result = await db.execute(
        select(LegalRecommendation).where(LegalRecommendation.id == recommendation_id)
    )
    rec = rec_result.scalar_one()

    ctx = await build_case_context(db, case_id)
    case_summary = ctx.build_summary()

    recs_data = rec.recommendations or {}
    recommendations_text = _format_recommendations(recs_data.get("recommendations", []))
    evidence_gaps = "\n".join(f"- {g}" for g in recs_data.get("evidence_gaps", [])) or "None identified"
    procedural_notes = "\n".join(f"- {n}" for n in recs_data.get("procedural_notes", [])) or "None"

    history_result = await db.execute(
        select(LegalChatMessage)
        .where(LegalChatMessage.recommendation_id == recommendation_id)
        .order_by(LegalChatMessage.created_at.desc())
        .limit(10)
    )
    history_msgs = list(reversed(history_result.scalars().all()))
    chat_history = _format_chat_history(history_msgs[:-1])

    rag_context = ""
    try:
        results = await search_legal_provisions(message, top_k=3)
        if results:
            parts = []
            for r in results:
                parts.append(f"[{r['act']}] Section {r.get('section_number', '')} - {r.get('heading', '')}\n{r['text'][:300]}")
            rag_context = "\n\n".join(parts)
    except Exception:
        pass

    if not rag_context:
        rag_context = "No additional provisions retrieved."

    ai_response = await _call_llm(
        case_summary=case_summary,
        recommendations_text=recommendations_text,
        evidence_gaps=evidence_gaps,
        procedural_notes=procedural_notes,
        rag_context=rag_context,
        chat_history=chat_history,
        user_message=message,
    )

    assistant_msg = LegalChatMessage(
        case_id=case_id,
        recommendation_id=recommendation_id,
        user_id=user_id,
        role=ChatRole.ASSISTANT,
        content=ai_response,
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)
    return assistant_msg


def _format_recommendations(recommendations: list[dict]) -> str:
    if not recommendations:
        return "No recommendations generated yet."
    parts = []
    for r in recommendations:
        section = r.get("section", "")
        act = r.get("act", "")
        title = r.get("title", "")
        explanation = r.get("explanation", "")
        confidence = r.get("confidence", 0)
        is_primary = r.get("is_primary", True)
        charge_type = "PRIMARY" if is_primary else "ALTERNATIVE"
        parts.append(f"[{charge_type}] {section} ({act}) - {title} [Confidence: {confidence:.0%}]\n  {explanation}")
    return "\n\n".join(parts)


def _format_chat_history(messages: list[LegalChatMessage]) -> str:
    if not messages:
        return "No previous conversation."
    parts = []
    for msg in messages:
        role = "Officer" if msg.role == ChatRole.USER else "CrimeGPT"
        parts.append(f"{role}: {msg.content}")
    return "\n".join(parts)


async def _call_llm(
    case_summary: str,
    recommendations_text: str,
    evidence_gaps: str,
    procedural_notes: str,
    rag_context: str,
    chat_history: str,
    user_message: str,
) -> str:
    try:
        from app.ai.llm_provider import get_llm, has_any_llm_key

        if not has_any_llm_key():
            return "AI service is not configured. Please contact your system administrator."

        llm = get_llm(temperature=0.3)
        prompt = LEGAL_FOLLOWUP_PROMPT.format(
            case_summary=case_summary[:3000],
            recommendations_text=recommendations_text[:3000],
            evidence_gaps=evidence_gaps[:1000],
            procedural_notes=procedural_notes[:1000],
            rag_context=rag_context[:2000],
            chat_history=chat_history[:2000],
            user_message=user_message,
        )
        response = await llm.ainvoke(prompt)
        return response.content
    except Exception:
        return (
            "I'm currently unable to process your question (service unavailable). "
            "Please try again later or contact your system administrator."
        )
